import tests.context

import pytest
import numpy as np
import os
import shutil

from tests.testing_utils              import (make_initialize_job, make_train_job, \
                                                make_serialized_job, make_split_job)
from core.utils.enums                 import (JobTypes, RawEventTypes, \
                                            ActionableEventTypes, MessageEventTypes)
from core.fed_avg_optimizer           import FederatedAveragingOptimizer
from core.cloud_connected_optimizer   import CloudConnectedOptimizer
from core.runner                      import DMLRunner
from core.configuration               import ConfigurationManager
from core.dataset_manager             import DatasetManager
from data.iterators                   import count_datapoints
from core.blockchain.blockchain_utils import TxEnum


@pytest.fixture(scope='session')
def config_manager():
    config_manager = ConfigurationManager()
    config_manager.bootstrap(
        config_filepath='tests/artifacts/fed_avg_optimizer/configuration.ini'
    )
    return config_manager

@pytest.fixture(scope='session')
def mnist_uuid():
    return 'd16c6e86-d103-4e71-8741-ee1f888d206c'

@pytest.fixture(scope='session')
def small_uuid():
    return 'dc1a2ae7-42c6-455d-a2d5-49bb9f30614e'

@pytest.fixture(scope='session')
def mnist_filepath():
    return 'tests/artifacts/runner_scheduler/mnist'

@pytest.fixture(scope='session')
def small_filepath():
    return 'tests/artifacts/runner_scheduler/test'

@pytest.fixture(scope='session')
def dataset_manager(config_manager):
    dataset_manager = DatasetManager(config_manager)
    dataset_manager.bootstrap()
    return dataset_manager

@pytest.fixture(scope='session')
def initialization_payload(small_uuid):
    serialized_job = make_serialized_job()
    new_session_event = {
        TxEnum.KEY.name: {"dataset_uuid": small_uuid, "label_column_name": "label"},
        TxEnum.CONTENT.name: {
            "optimizer_params": {"num_averages_per_round": 2, "max_rounds": 2},
            "serialized_job": serialized_job,
            "participants": ['0fcf9cbb-39df-4ad6-9042-a64c87fecfb3', 'd16c6e86-d103-4e71-8741-ee1f888d206c']
        }
    }
    return new_session_event

@pytest.fixture(scope='session')
def initialization_payload_cloud(small_uuid):
    serialized_job = make_serialized_job()
    serialized_job["job_uuid"] = "1234"
    new_session_event = {
        TxEnum.KEY.name: {"dataset_uuid": small_uuid, "label_column_name": "label"},
        TxEnum.CONTENT.name: {
            "optimizer_params": {
                "num_averages_per_round": 2, 
                "max_rounds": 2,
                "optimizer_type": "CLOUD_CONNECTED"
            },
            "serialized_job": serialized_job,
            "participants": ['0fcf9cbb-39df-4ad6-9042-a64c87fecfb3', 'd16c6e86-d103-4e71-8741-ee1f888d206c']
        }
    }
    return new_session_event

@pytest.fixture(scope='session')
def transformed_filepath():
    return 'tests/artifacts/fed_avg_optimizer/mnist'+'/transformed'

@pytest.fixture(scope='session')
def transformed_filepath_2():
    return 'tests/artifacts/fed_avg_optimizer/test'+'/transformed'

@pytest.fixture(scope='session', autouse=True)
def cleanup(transformed_filepath, transformed_filepath_2):
    # Will be executed before the first test
    yield
    # Will be executed after the last test
    if os.path.isdir(transformed_filepath):
        shutil.rmtree(transformed_filepath)
    if os.path.isdir(transformed_filepath_2):
        shutil.rmtree(transformed_filepath_2)

@pytest.fixture(scope='session')
def runner(config_manager):
    runner = DMLRunner(config_manager)
    return runner

@pytest.fixture(scope='session')
def init_dmlresult_obj(runner, small_filepath):
    initialize_job = make_initialize_job(small_filepath)
    result = runner.run_job(initialize_job)
    return result

@pytest.fixture(scope='session')
def split_dmlresult_obj(runner, mnist_filepath):
    split_job = make_split_job(mnist_filepath,)
    split_job.hyperparams['split'] = 0.75
    job_results = runner.run_job(split_job)
    return job_results

@pytest.fixture(scope='session')
def train_dmlresult_obj(runner, split_dmlresult_obj, init_dmlresult_obj, small_filepath):
    initial_weights = init_dmlresult_obj.results['weights']
    session_filepath = split_dmlresult_obj.results['session_filepath']
    datapoint_count = split_dmlresult_obj.results['datapoint_count']
    train_job = make_train_job(
                    initial_weights,
                    session_filepath,
                    datapoint_count
                )
    result = runner.run_job(train_job)
    return result

def test_cloudconn_optimizer_schedules_serving_after_training(initialization_payload_cloud, dataset_manager, init_dmlresult_obj, train_dmlresult_obj):
    optimizer = CloudConnectedOptimizer(
                    initialization_payload_cloud, 
                    dataset_manager
                )
    event_type, job_arr = optimizer.ask(RawEventTypes.JOB_DONE.name, init_dmlresult_obj)
    event_type, job_arr = optimizer.ask(RawEventTypes.JOB_DONE.name, train_dmlresult_obj)
    assert event_type == ActionableEventTypes.SCHEDULE_JOBS.name
    assert len(job_arr) == 2
    assert job_arr[0].job_type == JobTypes.JOB_COMM.name
    assert job_arr[1].job_type == JobTypes.JOB_STATS.name

def test_optimizer_fails_on_wrong_event_type(initialization_payload, dataset_manager):
    optimizer = FederatedAveragingOptimizer(
                    initialization_payload, 
                    dataset_manager
                )
    try:
        dummy_payload = {}
        _, _ = optimizer.ask("WRONG_EVENT_TYPE", dummy_payload)
        raise Exception("Optimizer should have failed!")
    except Exception as e:
        assert str(e) == "Invalid callback passed!"

def test_optimizer_can_kickoff(runner, initialization_payload, dataset_manager):
    optimizer = FederatedAveragingOptimizer(
                    initialization_payload, 
                    dataset_manager
                )
    event_type, job_arr = optimizer.kickoff()
    assert event_type == ActionableEventTypes.SCHEDULE_JOBS.name
    for job in job_arr:
        assert job.job_type == JobTypes.JOB_INIT.name or job.job_type == JobTypes.JOB_SPLIT.name

def test_optimizer_schedules_training_after_initialization(initialization_payload, dataset_manager, init_dmlresult_obj, split_dmlresult_obj):
    optimizer = FederatedAveragingOptimizer(
                    initialization_payload, 
                    dataset_manager
                )
    initial_weights = init_dmlresult_obj.results['weights']
    event_type, job_arr = optimizer.ask(RawEventTypes.JOB_DONE.name, init_dmlresult_obj)
    assert all(np.allclose(arr1, arr2) for arr1,arr2 in zip(optimizer.job_data["weights"], initial_weights))    
    assert event_type == ActionableEventTypes.NOTHING.name
    event_type, job_arr = optimizer.ask(RawEventTypes.JOB_DONE.name, split_dmlresult_obj)
    assert event_type == ActionableEventTypes.SCHEDULE_JOBS.name
    for job in job_arr:
        assert job.job_type == JobTypes.JOB_TRAIN.name

def test_optimizer_schedules_communication_after_training(initialization_payload, dataset_manager, init_dmlresult_obj, train_dmlresult_obj):
    optimizer = FederatedAveragingOptimizer(
                    initialization_payload, 
                    dataset_manager
                )
    event_type, job_arr = optimizer.ask(RawEventTypes.JOB_DONE.name, init_dmlresult_obj)
    trained_weights = train_dmlresult_obj.results['weights']
    event_type, job_arr = optimizer.ask(RawEventTypes.JOB_DONE.name, train_dmlresult_obj)
    assert all(np.allclose(arr1, arr2) for arr1,arr2 in zip(optimizer.job_data["weights"], trained_weights))
    assert event_type == ActionableEventTypes.SCHEDULE_JOBS.name
    for job in job_arr:
        assert job.job_type == JobTypes.JOB_COMM.name

# def test_optimizer_waits_to_average_until_trained(initialization_payload, train_dmlresult_obj, dataset_manager):
#     optimizer = FederatedAveragingOptimizer(initialization_payload, dataset_manager)
#     args = {
#         TxEnum.KEY.name: MessageEventTypes.NEW_WEIGHTS.name,
#         TxEnum.CONTENT.name: serialize_job(train_dmlresult_obj.job)
#     }
#     nothing, nothing_ = optimizer.ask(RawEventTypes.NEW_MESSAGE.name, args)
#     assert False
