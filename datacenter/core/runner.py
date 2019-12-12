import random
import uuid
import time
import os
import pandas as pd
import numpy as np
import requests
import json

from core.configuration import ConfigurationManager
from custom.keras import model_from_serialized, get_optimizer
from data.iterators import count_datapoints
from data.iterators import create_random_train_dataset_iterator
from data.iterators import create_random_test_dataset_iterator
from core.utils.keras import train_keras_model, validate_keras_model, calculate_gradients
from keras.models import load_model
from keras import backend as K

from core.utils.keras import serialize_weights, deserialize_weights
from core.utils.dmlresult import DMLResult
from core.utils.enums import JobTypes, callback_handler_no_default
import base64

import logging
# import logging as runner_logging

# runner_logging.basicConfig(level=runner_logging.DEBUG,
#                     format='[Runner] %(asctime)s %(levelname)s %(message)s')



class DMLRunner(object):
    """
    DML Runner

    This class manages the training and validation of a DML job. It trains or
    validate a specified machine learning model on a local dataset. An instance
    of this class has a one-to-one relationship with a DML job, and gets freed up
    for another DML job after executing the job. Once free, it can schedule a new
    DML job from any DML session and repeat the cycle.

    Note that this class does not schedule how jobs received should be executed
    nor listens to incoming jobs. This class only executes the jobs.

    """

    def __init__(self, config_manager):
        """
        Sets up the unique identifier of the DML Runner and the local dataset path.
        
        Sets up IPFS client for _communicate.
        """
        config = config_manager.get_config()
        self.iden = str(uuid.uuid4())[:8]
        self.config = dict(config.items("RUNNER"))
        self._port = config.getint('BLOCKCHAIN', 'http_port')
        self._server_url = config.get('RUNNER', 'server_url')
        self._dataset_path = config.get('GENERAL', 'dataset_path')
        self.JOB_CALLBACKS = {
            JobTypes.JOB_TRAIN.name: self._train,
            JobTypes.JOB_INIT.name: self._initialize,
            JobTypes.JOB_VAL.name: self._validate,
        }
        self.logger = logging.getLogger('Runner')
    
    # def configure(self, ipfs_client):
    #     """
    #     Sets up IPFS client for _communicate
    #     """
    #     self._client = ipfs_client

    def run_job(self, job):
        """
        Identifies a DMLJob type and executes it.

        If the runner is already executing a job, it silently does nothing.
        """
        assert job.job_type.upper() in self.JOB_CALLBACKS, \
            'DMLJob type ({0}) is not valid'.format(job.job_type)
        self.logger.info("Running job (type: {0})...".format(job.job_type))
        callback = callback_handler_no_default(
            job.job_type,
            self.JOB_CALLBACKS,
        )
        
        results = callback(job)
        results.session_id = job.session_id
        self.current_job = None
        self.logger.info("Finished running job! (type: {0})".format(job.job_type))
        return results

    def _set_up(self):
        assert self._dataset_path, \
            "Transformed training and test sets not created yet!"
        train_path = os.path.join(
                                self._dataset_path, 
                                'train.csv'
                            )
        test_path = os.path.join(
                                self._dataset_path, 
                                'test.csv'
                            )
        return train_path, test_path

    def _initialize(self, job):
        """
        Initializes and returns a DMLResult with the model
        weights as specified in the model.
        """
        assert job.framework_type in ['keras'], \
            "Model type '{0}' is not supported.".format(job.framework_type)
        self.logger.info("Initializing model...")
        if job.framework_type == 'keras':
            if job.h5_model_folder:
                h5_model_folder = job.h5_model_folder
                h5_model_filepath = os.path.join(h5_model_folder, 'model.h5')
                model = load_model(h5_model_filepath)
                gradients = job.gradients
                learning_rate = model.optimizer.lr
                weights = np.array(model.get_weights())
                new_weights = np.subtract(weights, gradients)
                model.set_weights(new_weights)
                model.save(h5_model_filepath)
            else:
                h5_model_folder = os.path.join('sessions', job.session_id)
                h5_model_filepath = os.path.join(h5_model_folder, 'model.h5')
                model = load_model(h5_model_filepath)
                print("Loaded model!")
                if not job.use_gradients:
                    print("Clearing model folder...")
                    os.remove(h5_model_filepath)
                    os.rmdir(h5_model_folder)
                    h5_model_folder = None
        print(h5_model_folder)
        print(h5_model_filepath)
        results = DMLResult(
            status='successful',
            job=job,
            results={
                'model': model,
                'h5_model_folder': h5_model_folder,
            },
            error_message="",
        )
        return results

    def _train(self, job):
        """
        Trains the specified machine learning model on all the local data,
        starting from the initial model state specified, until a stopping
        condition is met, and using the hyper-parameters specified.

        Returns a DMLResult with the updated model weights, the weighting factor
        omega, and stats about the training job.

        NOTE: Uses the same hyperparameters and labeler for training and
        validating during 'avg_type' of type 'val_acc'.

        NOTE2: Assumes 'job.weights' are the actual weights and not a path.
        """
        
        train_dataset_path, test_dataset_path = self._set_up()
        data_count_mappings = count_datapoints(self._dataset_path)

        # Get the right dataset iterator based on the averaging type.
        avg_type = job.hyperparams.get('averaging_type', 'data_size')
        batch_size = job.hyperparams['batch_size']
        assert avg_type in ['data_size', 'val_acc'], \
            "Averaging type '{0}' is not supported.".format(avg_type)
        self.logger.info("Training model...")
        if avg_type == 'data_size':
            dataset_iterator = create_random_train_dataset_iterator(
                train_dataset_path,
                batch_size=batch_size,
                infinite=False,
                num_epochs=job.hyperparams.get('epochs')
            )
        elif avg_type == 'val_acc':
            dataset_iterator = create_random_train_dataset_iterator(
                train_dataset_path,
                batch_size=batch_size,
            )
            test_dataset_iterator = create_random_test_dataset_iterator(
                test_dataset_path,
                batch_size=batch_size,
            )

        # Train the model the right way based on the model type.
        assert job.framework_type in ['keras'], \
            "Model type '{0}' is not supported.".format(job.framework_type)

        if job.framework_type == 'keras':
            trained_model, result_val = train_keras_model(
                job.model,
                dataset_iterator,
                data_count_mappings['train.csv'],
                job.hyperparams,
                self.config,
                gradients=job.use_gradients,
            )

        # Get the right omega based on the averaging type.
        if avg_type == 'data_size':
            omega = data_count_mappings['train.csv']
        elif avg_type == 'val_acc':
            val_stats = self._validate(
                job,
                custom_iterator=test_dataset_iterator
            ).results['val_stats']
            omega = val_stats['val_metric']['acc']
            train_stats.update(val_stats)
        trained_model.save("sessions/my_model.h5")
        with open("sessions/my_model.h5", mode='rb') as file:
            file_content = file.read()
            encoded_content = base64.b64encode(file_content)
            h5_model = encoded_content.decode('ascii')

        train_results = {
            'omega': omega,
        }

        if job.use_gradients:
            train_results['gradients'] = result_val
        else:
            train_results['h5_model'] = h5_model
            train_results['train_stats'] = result_val
            
        # new_weights_path = [weights.tolist() for weights in new_weights_path]
        #print(new_weights_path)
        # Return the results.
        # return new_weights_path, omega, train_stats
        results = DMLResult(
            status='successful',
            job=job,
            results=train_results,
            error_message="",
        )
        return results

    def _validate(self, job, custom_iterator=None):
        """
        Validates on all the local data the specified machine learning model at
        the state specified.

        Returns a DMLResult with the metrics returned by the model.

        NOTE: Assumes 'weights' are the actual weights and not a path.
        """
        self.logger.info("Validating model...")
        
        train_dataset_path, test_dataset_path = self._set_up(job)
        data_count = job.datapoint_count
        # Choose the dataset to validate on.
        batch_size = job.hyperparams['batch_size']
        split = job.hyperparams['split']
        if custom_iterator is None:
            dataset_iterator = create_random_test_dataset_iterator(
                test_dataset_path,
                batch_size=batch_size,
                labeler=job.label_column_name,
            )
        else:
            dataset_iterator = custom_iterator

        # Validate the model the right way based on the model type.
        assert job.framework_type in ['keras'], \
            "Model type '{0}' is not supported.".format(job.framework_type)
        if job.framework_type == 'keras':
            val_stats = validate_keras_model(
                job.serialized_model,
                job.weights,
                dataset_iterator,
                data_count*(1-split)
            )

        # Return the validation stats.
        results = DMLResult(
            status='successful',
            job=job,
            results={
                'val_stats': val_stats,
            },
            error_message="",
        )
        return results

    

    def _communicate(self, job):
        """
        Communicates a message to the blockchain using the Runner's
        IPFS client, puts the tx_receipt in DMLResult.
        """
        assert job.round_num, "Nonzero round number is needed for this message!"

        # tx_receipt = setter(
        #     client=self._client,
        #     key = content_to_ipfs(self._client, serialize_weights(job.key)),
        #     port = self._port,
        #     value = job.serialize_job(),
        #     round_num = job.round_num,
        #     state_append=state
        # )

        train_results = {
            "weights": job.weights,
            "omega": job.omega
        }
        job.websocket_client.send_new_weights(train_results, job.session_id)

        results = DMLResult(
            status='successful',
            job=job,
            error_message="",
        )
        return results

    def _post_statistics(self, job):
        """
        Posts statistics about a training job to a cloud server
        """
        assert job.statistics, "No statistics to be served"
        server_url = "{0}/{1}/{2}".format(self._server_url, job.job_uuid, job.dataset_uuid)
        response = requests.post(
            url=server_url,
            headers={'content-type': 'application/json'},
            json={
                'round_num': job.round_num,
                'dataset_stats': job.statistics
            }
        )
        response_dict = json.loads(response.text)
        results = DMLResult(
            status='successful',
            job=job,
            results={'receipt': response_dict['status']},
            error_message="",
        )
        return results

    def _split_data(self, job):
        """
        Takes in a job, which should have the raw filepath assigned.

        1. In each folder, aggregate all data.
        2. Create session folder in transformed folder, along with data folders
           in session folder.
        3. Shuffle each transformed data and perform train-test split on each. 
        4. Put each training and test set in corresponding data folders in 
           session folder.
        5. Update session filepath in job.
        """

        # 1. Extracts all of the raw data from raw data filepath
        assert job.raw_filepath, \
            "Raw data filepath has not been set!"
        files = os.listdir(job.raw_filepath)
        files = list(filter(lambda x: x.endswith('.csv'), files))
        assert len(files) == 1, \
            "Only supporting one file per dataset folder!"
        data_filepath = os.path.join(
                    job.raw_filepath,
                    files[0]
                )
        raw_data = pd.read_csv(data_filepath)

        # 2. Create transformed folder, if it doesn't exist.
        transformed_filepath = os.path.join(job.raw_filepath, "transformed")
        if not os.path.isdir(transformed_filepath):
            os.makedirs(transformed_filepath)

        # 3. Create session folder using timestamp and random characters.
        new_name = str(uuid.uuid4())
        session_filepath = os.path.join(transformed_filepath, new_name)
        os.makedirs(session_filepath)

        # 4. Retrieve train-test split from job.
        split = job.hyperparams['split']

        # 5. Shuffle raw data, then split into train and test set.
        raw_data = raw_data.sample(frac=1)
        split_index = int(len(raw_data)*split)
        train = raw_data.iloc[:split_index] 
        test = raw_data.iloc[split_index:]

        # 6. Create train.csv and test.csv in data folder.
        train.to_csv(
            os.path.join(session_filepath, 'train.csv'),
            index=False
        )

        test.to_csv(
            os.path.join(session_filepath, 'test.csv'),
            index=False
        )

        # 7. Get datapoint count to be used in future jobs
        datapoint_count = count_datapoints(session_filepath)

        # 8. Return job with assigned session folder filepath and
        #    datapoint count.
        results = DMLResult(
                    status='successful',
                    job=job,
                    results = {
                        'session_filepath': session_filepath,
                        'datapoint_count': datapoint_count
                    },
                    error_message=""
                )
        return results 
      
