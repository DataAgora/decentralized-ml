from models.keras_perceptron    import KerasPerceptron
from custom.keras               import get_optimizer
from core.utils.enums           import JobTypes, RawEventTypes
from core.utils.dmljob          import (DMLCommunicateJob, \
                                        DMLAverageJob, DMLInitializeJob, DMLSplitJob, \
                                        DMLTrainJob, DMLValidateJob)
from data.iterators             import count_datapoints

def make_dataset_path():
    return 'datasets/mnist'

def make_communicate_job(key, weights):
    job = DMLCommunicateJob(
        round_num=40,
        key=key,
        weights=weights,
        omega=1.0,
        sigma_omega=1.0
    )
    return job

def _make_model_json():
    m = KerasPerceptron(is_training=True)
    model_architecture = m.model.to_json()
    model_optimizer = get_optimizer(m.model)
    model_json = {
        "architecture": model_architecture,
        "optimizer": model_optimizer
    }
    return model_json

def make_initialize_job(raw_filepath=None, uuid=None):
    job = DMLInitializeJob(
        framework_type="keras",
        serialized_model=_make_model_json()
    )
    return job

def make_split_job(raw_filepath):
    job = DMLSplitJob(
        hyperparams=_make_hyperparams(),
        raw_filepath=raw_filepath
    )
    return job

def _make_hyperparams(split=0.004):
    hyperparams = {
        'averaging_type': 'data_size',
        'batch_size': 4,
        'epochs': 1,
        'split': 1,
    }
    return hyperparams

def make_train_job(initial_weights, session_filepath, datapoint_count):
    job = DMLTrainJob(
        datapoint_count=datapoint_count,
        hyperparams=_make_hyperparams(),
        label_column_name='label',
        framework_type="keras",
        serialized_model=_make_model_json(),
        weights=initial_weights,
        session_filepath=session_filepath
    )
    return job

def make_serialized_job():
    serialized_job = {
        "framework_type": "keras",
        "serialized_model": _make_model_json(),
        "hyperparams": _make_hyperparams()
    }
    return serialized_job

# def make_serialized_job_with_uuid(uuid):
#     initialize_job = make_initialize_job(uuid=uuid)
#     serialized_job = initialize_job.serialize_job()
#     return serialized_job

def make_validate_job(new_weights, \
    session_filepath, datapoint_count):
    job = DMLValidateJob(
        datapoint_count=datapoint_count,
        hyperparams=_make_hyperparams(),
        label_column_name='label',
        framework_type="keras",
        serialized_model=_make_model_json(),
        weights=new_weights,
        session_filepath=session_filepath
    )
    return job
