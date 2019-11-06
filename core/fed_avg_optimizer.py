
import time
import requests

from core.utils.enums 					import ActionableEventTypes, RawEventTypes, MessageEventTypes
from core.utils.enums 					import JobTypes, callback_handler_no_default
from core.utils.dmljob 					import (DMLJob, DMLAverageJob, DMLCommunicateJob, DMLServerJob, \
												DMLInitializeJob, DMLSplitJob, DMLTrainJob, DMLValidateJob)
from core.utils.keras 					import serialize_weights, deserialize_weights
from core.utils.dmlresult 				import DMLResult

import logging


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

	def __init__(self, runner):
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
		self.logger = logging.getLogger("FedAvgOptimizer")
		self.logger.info("Setting up Optimizer...")
		self.job_data = {}
		self.runner = runner
		
		self.LEVEL1_CALLBACKS = {
			RawEventTypes.JOB_DONE.name: self._handle_job_done,
			RawEventTypes.NEW_MESSAGE.name: self._handle_new_info,
		}
		self.LEVEL2_JOB_DONE_CALLBACKS = {
			JobTypes.JOB_TRAIN.name: self._done_training,
			JobTypes.JOB_INIT.name: self._done_initializing,
			JobTypes.JOB_COMM.name: self._done_communicating,
			#JobTypes.JOB_SPLIT.name: self._done_split,
		}
		self.LEVEL_2_NEW_INFO_CALLBACKS = {
			MessageEventTypes.TERMINATE.name: self._received_termination,
			MessageEventTypes.NEW_SESSION.name: self._do_nothing,
		}

		self.logger.info("Optimizer has been set up!")

	def received_new_message(self, serialized_job):
		session_id = serialized_job.get("session_id")
		round = serialized_job.get("round")
		if self.job_data.get("curr_round", 0) + 1 >= round:
			self.logger.error("Received job for unexpected round {}, ignoring...".format(round))
			return {"success": False}

		self.logger.info("Starting round: {}".format(round))

		if 'session_id' in self.job_data:
			if self.job_data['session_id'] 1= serialized_job['session_id']:
				self.logger.error("Received new session while in the middle of another session!")
				return {"success": False}
			return self._continue_training(serialized_job, session_id)
		else:
			return self.new_job(serialized_job, session_id)

	def _continue_training(self, serialized_job, session_id):
		self.job_data['h5_model'] = serialized_job.get("h5_model")
		self.job_data["curr_round"] = serialized_job.get("round")
		self.job_data["gradients"] = serialized_job.get("gradients")
		return self.kickoff(session_id)

	def new_job(self, serialized_job, session_id):
		self.job_data["session_id"] = serialized_job.get("session_id")
		self.job_data["framework_type"] = serialized_job.get("framework_type", "keras")
		#self.job_data["serialized_model"] = serialized_job.get("serialized_model")
		self.job_data["hyperparams"] = serialized_job.get("hyperparams")
		self.job_data["label_column_name"] = serialized_job.get("hyperparams").get("label_column_name")
		self.job_data["sigma_omega"] = 0
		# self.num_averages_per_round = optimizer_params.get('num_averages_per_round')
		self.job_data["curr_round"] = 1
		self.job_data["use_gradients"] = serialized_job.get("use_gradients")
		self.job_data["h5_model_filepath"] = None
		self.job_data["gradients"] = None
		h5_model = serialized_job.get("h5_model")
		
		# Set other participants so that the optimizer knows which other nodes 
		# it's expected to hear messages from for future session_info messages
		# participants = job_info.get('participants')
		# self.other_participants = [participant for participant in participants
		# 							if participant != self.job_data["dataset_uuid"]]
		return self.kickoff(session_id, h5_model=h5_model)
		

	def kickoff(self, session_id, h5_model=None):
		"""
		Kickoff method used at the beginning of a DML Session.

		Creates a job that transforms and splits the dataset, and also
		randomly initializes the model.
		"""
		init_job = DMLInitializeJob(framework_type=self.job_data["framework_type"],
									use_gradients=self.job_data["use_gradients"],
									h5_model=h5_model,
									h5_model_filepath=self.job_data["h5_model_filepath"],
									gradients=self.job_data["gradients"])
		init_job.session_id = session_id
		# split_job = DMLSplitJob(hyperparams=self.job_data["hyperparams"],
		# 						raw_filepath=self.job_data["raw_filepath"])
		# split_job.session_id = session_id
		# job_arr.append(split_job)
		dmlresult_obj = self.runner.run_job(init_job)
		return self._handle_job_done(dmlresult_obj)

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
		self.logger.info("Job completed: {}".format(dmlresult_obj.job.job_type))
		return callback(dmlresult_obj)

	def _done_initializing(self, dmlresult_obj):
		"""
		"LEVEL 2" Callback for a initialization job that just completed. Returns
		a DML Job of type train unless transforming and splitting is not yet done
		and modifies the current state of the job.
		"""
		session_id = dmlresult_obj.job.session_id
		self.job_data['h5_model_filepath'] = dmlresult_obj.results.get('h5_model_filepath')
		train_job = DMLTrainJob(
			hyperparams=self.job_data["hyperparams"],
			label_column_name=self.job_data["label_column_name"],
			framework_type=self.job_data["framework_type"],
			model= dmlresult_obj.results.get('model'),
			use_gradients=self.job_data["use_gradients"],
		)
		train_job.session_id = session_id
		dmlresult_obj = self.runner.run_job(train_job)
		return self._handle_job_done(dmlresult_obj)

	# def _done_split(self, dmlresult_obj):
	# 	"""
	# 	"LEVEL 2" Callback for a split job that just finished.
	# 	Returns a DML Job of type train unless initialization is not yet done
	# 	and modifies the current state of the job.
	# 	"""
	# 	session_id = dmlresult_obj.job.session_id
	# 	self.job_data["session_filepath"] = dmlresult_obj.results['session_filepath']
	# 	self.job_data["datapoint_count"] = dmlresult_obj.results['datapoint_count']
	# 	if self.job_data["initialization_complete"]:
	# 		train_job = DMLTrainJob(
	# 			datapoint_count=self.job_data["datapoint_count"],
	# 			hyperparams=self.job_data["hyperparams"],
	# 			label_column_name=self.job_data["label_column_name"],
	# 			framework_type=self.job_data["framework_type"],
	# 			serialized_model=self.job_data["serialized_model"],
	# 			weights=self.job_data["weights"],
	# 			session_filepath=self.job_data["session_filepath"]
	# 		)
	# 		train_job.session_id = session_id
	# 		return ActionableEventTypes.SCHEDULE_JOBS.name, [train_job]
	# 	else:
	# 		self.job_data["initialization_complete"] = True
	# 		return ActionableEventTypes.NOTHING.name, None

	def _done_training(self, dmlresult_obj):
		"""
		"LEVEL 2" Callback for a training job that just completed. Returns a
		DML Job of type communication and modifies the current state of the job.

		NOTE: Assumes that the training succeeded. In the future, we may care
		about a degree of accuracy needing to be reached before updating the
		weights.
		"""
		results = dmlresult_obj.results
		results["success"] = True
		return results

	def _done_communicating(self, dmlresult_obj):
		"""
		"LEVEL 2" Callback for a Communication job.
		"""
		return ActionableEventTypes.NOTHING.name, None

	def _done_validating(self, dmlresult_obj):
		self.logger.info("Validation accuracy: {}".format(dmlresult_obj.results['val_stats']))
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

	def _update_weights(self, weights, session_id):
		"""
		Helper function to update the weights in the optimizer's currently
		stored DML Job, therefore ensuring that any future DML Jobs will operate
		with the correct weights. Mutates, does not return anything.
		"""
		self.job_data["weights"] = weights

	def _update_old_weights(self, session_id):
		"""
		Helper function to update the old_weights instance variable.
		"""
		self.old_weights = self.job_data["weights"]

	def _do_nothing(self, payload):
		"""
		Do nothing in case this optimizer heard a new session.
		"""
		return ActionableEventTypes.NOTHING.name, None
