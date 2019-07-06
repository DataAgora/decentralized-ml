import logging
import time
import requests

from core.utils.enums 					import ActionableEventTypes, RawEventTypes, MessageEventTypes
from core.utils.enums 					import JobTypes, callback_handler_no_default
from core.utils.dmljob 					import (DMLJob, DMLAverageJob, DMLCommunicateJob, DMLServerJob, \
												DMLInitializeJob, DMLSplitJob, DMLTrainJob, DMLValidateJob)
from core.utils.keras 					import serialize_weights, deserialize_weights
from core.utils.dmlresult 				import DMLResult
from core.blockchain.blockchain_utils	import TxEnum, content_to_ipfs


logging.basicConfig(level=logging.DEBUG,
	format='[FedAvgOpt] %(asctime)s %(levelname)s %(message)s')

class FederatedAveragingOptimizer(object):
	"""
	Federated Averaging Optimizer

	Implements the Federated Averaging algorithm (with some tweaks) and acts as
	a "brain" or decision making component for the service. This class is
	tightly integrated with the Communication Manager, and serves as an
	abstraction between routing messages internally and making decisions on
	what messages to route and to where.

	This particular optimizer works with callbacks:

		- There are "LEVEL 1" callbacks, which represent the types of Raw Events
	  	that the Optimizer needs to process.

		- There also are "LEVEL 2" callbacks, which represent a further breakdown
	  	of the "LEVEL 1" callbacks so that the Optimizer transform the event into
	  	a meaningful DML Job that can be executed by the Execution Pipeline.

	"""

	def __init__(self, websocket_clients):
		"""
		Initializes the basic optimizer, which does not communicate with
		the status_server or with Explora.

		Expects the `initialization_payload` dict to contain two dicts:

			- data-provider specific information, incl. dataset_uuid etc.

			- job specific information

				- `serialized_job`: the serialized DML Job

				- `optimizer_params`: the optimizer parameters (dict) needed to
				initialize this optimizer (should contain the max_rounds and
				num_averages_per_round)
		
		num_averages_per_round(int): how many weights this optimizer needs to incorporate
		into its weighted running average before it's "heard enough" 
		and can move on to training
		max_rounds(int): how many rounds of fed learning this optimizer wants to do
		"""
		logging.info("Setting up Optimizer...")
		self.job_data = {}

		self.websocket_clients = websocket_clients

		for repo in websocket_clients:
			self.job_data[repo] = {}
		
		self.LEVEL1_CALLBACKS = {
			RawEventTypes.JOB_DONE.name: self._handle_job_done,
			RawEventTypes.NEW_MESSAGE.name: self._handle_new_info,
		}
		self.LEVEL2_JOB_DONE_CALLBACKS = {
			JobTypes.JOB_TRAIN.name: self._done_training,
			JobTypes.JOB_INIT.name: self._done_initializing,
			JobTypes.JOB_COMM.name: self._done_communicating,
			JobTypes.JOB_SPLIT.name: self._done_split,
		}
		self.LEVEL_2_NEW_INFO_CALLBACKS = {
			MessageEventTypes.TERMINATE.name: self._received_termination,
			MessageEventTypes.NEW_SESSION.name: self._do_nothing,
		}

		logging.info("Optimizer has been set up!")

	def received_new_message(self, serialized_job, repo_id, dataset_manager):
		url = "http://" + repo_id + ".au4c4pd2ch.us-west-1.elasticbeanstalk.com/model/model.json"
		response = requests.get(url)
		print(response.text)

		if self.job_data[repo_id]:
			self.job_data[repo_id]["serialized_model"] = response.text
			return self._continue_training(repo_id)
		else:
			self.job_data[repo_id]["serialized_model"] = response.text
			return self.new_job(serialized_job, repo_id, dataset_manager)


	def new_job(self, serialized_job, repo_id, dataset_manager):
		self.job_data[repo_id]["session_id"] = serialized_job.get("session_id")
		self.job_data[repo_id]["framework_type"] = serialized_job.get("framework_type", "keras")
		#self.job_data["serialized_model"] = serialized_job.get("serialized_model")
		self.job_data[repo_id]["hyperparams"] = serialized_job.get("hyperparams")
		self.job_data[repo_id]["label_column_name"] = serialized_job.get("hyperparams").get("label_column_name")
		self.job_data[repo_id]["raw_filepath"] = dataset_manager.get_mappings()[repo_id]
		self.job_data[repo_id]["sigma_omega"] = 0
		# self.num_averages_per_round = optimizer_params.get('num_averages_per_round')
		self.job_data[repo_id]["curr_round"] = 1
		self.job_data[repo_id]["initialization_complete"] = False
		# Set other participants so that the optimizer knows which other nodes 
		# it's expected to hear messages from for future session_info messages
		# participants = job_info.get('participants')
		# self.other_participants = [participant for participant in participants
		# 							if participant != self.job_data["dataset_uuid"]]
		return self.kickoff(repo_id)
		

	def kickoff(self, repo_id):
		"""
		Kickoff method used at the beginning of a DML Session.

		Creates a job that transforms and splits the dataset, and also
		randomly initializes the model.
		"""
		job_arr = []
		init_job = DMLInitializeJob(framework_type=self.job_data[repo_id]["framework_type"],
									serialized_model=self.job_data[repo_id]["serialized_model"])
		init_job.repo_id = repo_id
		job_arr.append(init_job)
		split_job = DMLSplitJob(hyperparams=self.job_data[repo_id]["hyperparams"],
								raw_filepath=self.job_data[repo_id]["raw_filepath"])
		split_job.repo_id = repo_id
		job_arr.append(split_job)
		return ActionableEventTypes.SCHEDULE_JOBS.name, job_arr

	def ask(self, event_type, payload):
		"""
		Processes an event_type by calling the corresponding "LEVEL 1" Callback.
		"""
		callback = callback_handler_no_default(event_type, self.LEVEL1_CALLBACKS)
		return callback(payload)

	# Handlers for job completed in the execution pipeline

	def _handle_job_done(self, dmlresult_obj):
		"""
		"LEVEL 1" Callback that handles the conversion of a DML Result into a
		new DML Job by calling the appropriate "LEVEL 2" Callback.
		"""
		assert isinstance(dmlresult_obj, DMLResult)
		callback = callback_handler_no_default(
			dmlresult_obj.job.job_type,
			self.LEVEL2_JOB_DONE_CALLBACKS
		)
		logging.info("Job completed: {}".format(dmlresult_obj.job.job_type))
		return callback(dmlresult_obj)

	def _done_initializing(self, dmlresult_obj):
		"""
		"LEVEL 2" Callback for a initialization job that just completed. Returns
		a DML Job of type train unless transforming and splitting is not yet done
		and modifies the current state of the job.
		"""
		new_weights = dmlresult_obj.results.get('weights')
		self._update_weights(new_weights)
		if self.job_data[repo_id]["initialization_complete"]:
			repo_id = dmlresult_obj.repo_id
			train_job = DMLTrainJob(
				datapoint_count=self.job_data[repo_id]["datapoint_count"],
				hyperparams=self.job_data[repo_id]["hyperparams"],
				label_column_name=self.job_data[repo_id]["label_column_name"],
				framework_type=self.job_data[repo_id]["framework_type"],
				serialized_model=self.job_data[repo_id]["serialized_model"],
				weights=self.job_data[repo_id]["weights"],
				session_filepath=self.job_data[repo_id]["session_filepath"]
			)
			train_job.repo_id = repo_id
			return ActionableEventTypes.SCHEDULE_JOBS.name, [train_job]
		else:
			self.job_data[repo_id]["initialization_complete"] = True
			return ActionableEventTypes.NOTHING.name, None

	def _done_split(self, dmlresult_obj):
		"""
		"LEVEL 2" Callback for a split job that just finished.
		Returns a DML Job of type train unless initialization is not yet done
		and modifies the current state of the job.
		"""
		repo_id = dmlresult_obj.repo_id
		self.job_data[repo_id]["session_filepath"] = dmlresult_obj.results['session_filepath']
		self.job_data[repo_id]["datapoint_count"] = dmlresult_obj.results['datapoint_count']
		if self.job_data[repo_id]["initialization_complete"]:
			train_job = DMLTrainJob(
				datapoint_count=self.job_data[repo_id]["datapoint_count"],
				hyperparams=self.job_data[repo_id]["hyperparams"],
				label_column_name=self.job_data[repo_id]["label_column_name"],
				framework_type=self.job_data[repo_id]["framework_type"],
				serialized_model=self.job_data[repo_id]["serialized_model"],
				weights=self.job_data[repo_id]["weights"],
				session_filepath=self.job_data[repo_id]["session_filepath"]
			)
			train_job.repo_id = repo_id
			return ActionableEventTypes.SCHEDULE_JOBS.name, [train_job]
		else:
			self.job_data[repo_id]["initialization_complete"] = True
			return ActionableEventTypes.NOTHING.name, None

	def _done_training(self, dmlresult_obj):
		"""
		"LEVEL 2" Callback for a training job that just completed. Returns a
		DML Job of type communication and modifies the current state of the job.

		NOTE: Assumes that the training succeeded. In the future, we may care
		about a degree of accuracy needing to be reached before updating the
		weights.
		"""
		repo_id = dmlresult_obj.repo_id
		comm_job = DMLCommunicateJob(
			# TODO: Consider synchronization issues
			round_num=self.curr_round,
			weights=dmlresult_obj.results.get('weights'),
			omega=dmlresult_obj.results.get('omega'),
			session_id=self.job_data[repo_id].get("session_id")
		)
		comm_job.repo_id = repo_id
		comm_job.websocket_client = self.websocket_clients[repo_id]
		comm_job.loop = self.websocket_clients["loop"]
		return ActionableEventTypes.SCHEDULE_JOBS.name, [comm_job]

	def _done_communicating(self, dmlresult_obj):
		"""
		"LEVEL 2" Callback for a Communication job.
		"""
		return ActionableEventTypes.NOTHING.name, None

	def _done_validating(self, dmlresult_obj):
		logging.info("Validation accuracy: {}".format(dmlresult_obj.results['val_stats']))
		return ActionableEventTypes.TERMINATE.name, None
	# Handlers for new information from the gateway

	def _handle_new_info(self, payload):
		"""
		"LEVEL 1" Callback to handle new information from the blockchain.
		Payload structure should be:
		{TxEnum.KEY.name: <e.g. NEW_WEIGHTS>, 
		TxEnum.CONTENT.name: <e.g. weights>}	
		"""
		# TODO: Some assert on the payload, like in `_handle_job_done()`.
		callback = callback_handler_no_default(
			payload[TxEnum.KEY.name],
			self.LEVEL_2_NEW_INFO_CALLBACKS
		)
		return callback(payload)

	def _received_termination(self, payload):
		"""
		"LEVEL 2" Callback for a termination message received by the service
		from the blockchain.
		"""
		return ActionableEventTypes.TERMINATE.name, None

	# Helper functions

	def _update_weights(self, weights):
		"""
		Helper function to update the weights in the optimizer's currently
		stored DML Job, therefore ensuring that any future DML Jobs will operate
		with the correct weights. Mutates, does not return anything.
		"""
		self.job_data[repo_id]["weights"] = weights

	def _update_old_weights(self):
		"""
		Helper function to update the old_weights instance variable.
		"""
		self.old_weights = self.job_data[repo_id]["weights"]

	def _do_nothing(self, payload):
		"""
		Do nothing in case this optimizer heard a new session.
		"""
		return ActionableEventTypes.NOTHING.name, None
