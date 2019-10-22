from copy import deepcopy
import numpy as np

from core.utils.keras import serialize_weights, deserialize_weights
from core.utils.enums import JobTypes


class DMLJob(object):
    """
    DML Job

    This class represents a generic job that the Scheduler and Runners can
    execute. The job has some information that every job_type needs, but the
    rest of the information is stored in type-specific job objects.

    """

    def __init__(
        self,
        job_type        ):
        """
        Initializes a DML Job object.

        Args:
            job_type (str): the job type.
        """
        self.job_type = job_type
    
    def copy_constructor(self):
        newjob = deepcopy(self)
        return newjob
    
    def serialize_job(self):
        return self.__dict__

class DMLTrainJob(DMLJob):
    """
    DML Job for Training

    Holds information specifically needed for training
    """
    def __init__(
        self,
        hyperparams,
        label_column_name,
        framework_type,
        model,
        ):
        """
        Initializes a DML Train Job object.

        Args:
            job_type (str): the job type.
            serialized_model (dict): the model to train in a serialized format.
            framework_type (str): the type of framework the model is in [keras].
            weights (list): list of np.arrays representing the weights of a model.
            hyperparams (dict): hyperparameters for training/validating a model.
            label_column_name (str): string that represents which column of the
                                     transformed dataset contains the labels for
                                     supervised training.
            datapoint_count (int): Number of datapoints after applying
                                   transform function.
            session_filepath (str): the filepath to the folder that contains
                                    the raw data after applying the transform
                                    function and training-test split. Assumes
                                    `train.csv` and `test.csv` are in folder.
        """
        self.job_type = JobTypes.JOB_TRAIN.name
        self.hyperparams = hyperparams
        self.label_column_name = label_column_name
        self.framework_type = framework_type
        self.model = model

class DMLValidateJob(DMLJob):
    """
    DML Job for Validation

    Holds information specifically needed for validation
    """
    def __init__(
        self,
        datapoint_count,
        hyperparams,
        label_column_name,
        framework_type,
        serialized_model,
        weights,
        session_filepath
        ):
        """
        Initializes a DML Validation Job object.

        Args:
            job_type (str): the job type.
            serialized_model (dict): the model to train in a serialized format.
            framework_type (str): the type of framework the model is in [keras].
            weights (list): list of np.arrays representing the weights of a model.
            hyperparams (dict): hyperparameters for training/validating a model.
            label_column_name (str): string that represents which column of the
                                     transformed dataset contains the labels for
                                     supervised training.
            datapoint_count (int): Number of datapoints after applying
                                   transform function.
            session_filepath (str): the filepath to the folder that contains
                                    the raw data after applying the transform
                                    function and training-test split. Assumes
                                    `train.csv` and `test.csv` are in folder.
        """
        self.job_type = JobTypes.JOB_VAL.name
        self.datapoint_count = datapoint_count
        self.hyperparams = hyperparams
        self.label_column_name = label_column_name
        self.framework_type = framework_type
        self.serialized_model = serialized_model
        self.weights = weights
        self.session_filepath = session_filepath

class DMLInitializeJob(DMLJob):
    """
    DML Job for Initialization

    Holds information specifically needed for initialization
    """
    def __init__(
        self,
        framework_type,
        h5_model,
        ):
        """
        Initializes a DML initialization Job object.

        Args:
            job_type (str): the job type.
            serialized_model (dict): the model to train in a serialized format.
            framework_type (str): the type of framework the model is in [keras].
        """
        self.job_type = JobTypes.JOB_INIT.name
        self.framework_type = framework_type
        self.h5_model = h5_model
    
    def serialize_job(self):
        """
        Serializes a DML Job object into a dictionary.

        Returns:
            dict: The serialized version of the DML Job.
        """
        return {
            'serialized_model': self.serialized_model,
            'job_type': self.job_type,
            'framework_type': self.framework_type,
        }

class DMLCommunicateJob(DMLJob):
    """
    DML Job for Communication

    Holds information specifically needed for communication
    """
    def __init__(
        self,
        round_num,
        weights,
        omega,
        session_id
        ):
        """
        Initializes a DML Communicate Job object.

        Args:
            key (list): list of np.arrays representing the 'key' model
            weights (list): list of np.arrays representing the weights of a model.
            round_num (int): the index of the round in DML which this job is for
        """
        self.job_type = JobTypes.JOB_COMM.name
        self.round_num = round_num
        self.weights = weights
        self.omega = omega
        self.session_id = session_id

    def serialize_job(self):
        """
        Serializes a DML Job object into a dictionary.

        Returns:
            dict: The serialized version of the DML Job.
        """
        weights = serialize_weights(self.weights)
        return {
            'weights': weights,
            'job_type': self.job_type,
            'omega': self.omega,
            'sigma_omega': self.sigma_omega,
        }

class DMLSplitJob(DMLJob):
    """
    DML Job for Splitting Data

    Holds information specifically needed for splitting data

    """

    def __init__(
        self,
        hyperparams,
        raw_filepath
        ):
        """
        Initializes a DML Split Job object.

        Args:
            hyperparams (dict): hyperparameters for training/validating a model.
            raw_filepath (str): the filepath to the folder that contains the
                                raw data before transform and training-test  
                                split. Only one dataset file supported per
                                folder at the moment.
        """
        self.job_type = JobTypes.JOB_SPLIT.name
        self.hyperparams = hyperparams
        self.raw_filepath = raw_filepath

class DMLAverageJob(DMLJob):
    """
    DML Job for Averaging

    Holds information specifically needed for running weighted average

    """

    def __init__(
        self,
        omega,
        sigma_omega,
        weights,
        new_weights
        ):
        """
        Initializes a DML Average Job object.

        Args:
            weights (list): list of np.arrays representing the weights of a model.
            new_weights (list): list of np.arrays representing the weights that
                                should be averaged with 'weights'
            omega (float): the weight given to new_weights in weighted averaging
            sigma_omega (float): the sum of omega's incorporated into weighted
                                averaging so far. Kept in the DMLJob to allow the
                                weighted average to be unrolled.
        """
        self.job_type = JobTypes.JOB_AVG.name
        self.weights = weights
        self.omega = omega
        self.sigma_omega = sigma_omega
        self.new_weights = new_weights

class DMLServerJob(DMLJob):
    """
    DML Job for submitting Statistics

    Holds information specifically needed for submitting statistics

    """

    def __init__(
        self,
        job_uuid,
        dataset_uuid,
        round_num,
        statistics
        ):
        """
        Initializes a DML Server Job object.

        Args:
            uuid (str): uuid of the job for the server to identify.
            statistics (dict): statistics about the training process which just
                                finished, to be sent to the server
        """
        self.job_type = JobTypes.JOB_STATS.name
        self.job_uuid = job_uuid
        self.dataset_uuid = dataset_uuid
        self.round_num = round_num
        self.statistics = statistics
