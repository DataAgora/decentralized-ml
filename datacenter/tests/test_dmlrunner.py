import tests.context

import pytest
import numpy as np
import pandas as pd
import os
import shutil
import ipfsapi

from core.runner                import DMLRunner
from core.configuration         import ConfigurationManager
from core.dataset_manager       import DatasetManager
from core.utils.keras           import serialize_weights, deserialize_weights
from core.utils.enums           import JobTypes
from tests.testing_utils        import make_initialize_job, make_communicate_job
from tests.testing_utils        import make_train_job, make_validate_job
from tests.testing_utils        import make_split_job
from core.utils.dmljob          import DMLAverageJob, DMLServerJob
from core.blockchain.blockchain_gateway import BlockchainGateway
from core.blockchain.blockchain_utils   import setter

@pytest.fixture(scope='session')
def transformed_filepath():
    return 'tests/artifacts/runner_scheduler/mnist'+'/transformed'

@pytest.fixture(scope='session')
def transformed_filepath_2():
    return 'tests/artifacts/runner_scheduler/test'+'/transformed'

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
def communication_manager():		
    class MockCommunicationManager:
        def __init__(self):
            self.dummy1 = None
            self.dummy2 = None
        def inform(self, dummy1, dummy2):
            self.dummy1 = dummy1
            self.dummy2 = dummy2
    return MockCommunicationManager()

@pytest.fixture(scope='session')
def config_manager():
    config_manager = ConfigurationManager()
    config_manager.bootstrap(
        config_filepath='tests/artifacts/runner_scheduler/configuration.ini')
    return config_manager

@pytest.fixture(scope='session')
def ipfs_client(config_manager):
    config = config_manager.get_config()
    return ipfsapi.connect(config.get('BLOCKCHAIN', 'host'), 
                            config.getint('BLOCKCHAIN', 'ipfs_port'))

@pytest.fixture(scope='session')
def blockchain_gateway(config_manager, communication_manager, ipfs_client, dataset_manager):
    blockchain_gateway = BlockchainGateway()
    blockchain_gateway.configure(config_manager, communication_manager, ipfs_client, dataset_manager)
    return blockchain_gateway

@pytest.fixture(scope='session')
def mnist_filepath():
    return 'tests/artifacts/runner_scheduler/mnist'

@pytest.fixture(scope='session')
def small_filepath():
    return 'tests/artifacts/runner_scheduler/test'

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

@pytest.fixture(scope='session')
def dataset_manager(config_manager):
    dataset_manager = DatasetManager(config_manager)
    dataset_manager.bootstrap()
    return dataset_manager

@pytest.fixture(scope='session')
def runner(config_manager, ipfs_client):
    runner = DMLRunner(config_manager)
    runner.configure(ipfs_client=ipfs_client)
    return runner

def test_dmlrunner_status_server_post(runner, train_dmlresult_obj):
    server_job = DMLServerJob(job_uuid = "pandata", 
                            statistics=train_dmlresult_obj.results.get('train_stats'),
                            dataset_uuid = "sucks",
                            round_num = 40)
    result = runner.run_job(server_job).results
    assert result['receipt'] == 'success', 'POST failed!'

def test_dmlrunner_uniform_initialization(runner):
    initialize_job = make_initialize_job(small_filepath)
    result = runner.run_job(initialize_job).results
    first_weights = result['weights']
    initialize_job = make_initialize_job(small_filepath)
    result = runner.run_job(initialize_job).results
    second_weights = result['weights']
    assert all(np.allclose(arr1, arr2) for arr1,arr2 in zip(first_weights, second_weights))

def test_dmlrunner_communicate_job(runner, train_dmlresult_obj, blockchain_gateway):
    comm_job = make_communicate_job("testkey", "testweights")
    # now gateway should know the current state, which should be nothing
    assert len(blockchain_gateway.state) == 0
    # now we'll setter and hopefully append to the gateway's state
    result = runner.run_job(job=comm_job, state=blockchain_gateway.state)
    assert result.results["receipt"]
    # since we've appended to the state, it shouldn't be None
    assert len(blockchain_gateway.state) == 1

def test_dmlrunner_initialize_job_returns_list_of_nparray(init_dmlresult_obj):
    assert init_dmlresult_obj.status == 'successful'
    results = init_dmlresult_obj.results
    initial_weights = results['weights']
    assert init_dmlresult_obj.job.job_type is JobTypes.JOB_INIT.name
    assert type(initial_weights) == list
    assert type(initial_weights[0]) == np.ndarray

def test_dmlrunner_transform_and_split( \
        runner, small_filepath):
    split_job = make_split_job(small_filepath)
    split_job.hyperparams['split'] = 0.75
    job_results = runner.run_job(split_job)
    session_filepath = job_results.results['session_filepath']
    assert os.path.isdir(session_filepath), \
        "Session folder does not exist!"
    train_filepath = os.path.join(session_filepath, 'train.csv')
    test_filepath = os.path.join(session_filepath, 'test.csv')
    assert os.path.isfile(train_filepath) and os.path.isfile(test_filepath), \
        "Training and test set not created!"
    train = pd.read_csv(train_filepath)
    test = pd.read_csv(test_filepath)
    assert len(train) == 6 and len(test) == 2, \
        "Train test split was not performed correctly."

def test_dmlrunner_train_job_returns_weights_omega_and_stats( \
        train_dmlresult_obj):
    result = train_dmlresult_obj
    results = result.results
    new_weights = results['weights']
    omega = results['omega']
    train_stats = results['train_stats']
    assert result.job.job_type is JobTypes.JOB_TRAIN.name
    assert type(new_weights) == list
    assert type(new_weights[0]) == np.ndarray
    assert type(omega) == int or type(omega) == float
    assert type(train_stats) == dict

def test_dmlrunner_same_train_job_with_split_1( \
        runner, mnist_filepath):
    split_job = make_split_job(mnist_filepath)
    split_job.hyperparams['split'] = 1
    job_results = runner.run_job(split_job)
    session_filepath = job_results.results['session_filepath']
    datapoint_count = job_results.results['datapoint_count']
    initialize_job = make_initialize_job()
    initial_weights = runner.run_job(initialize_job).results['weights']
    train_job = make_train_job(
                    initial_weights, 
                    session_filepath,
                    datapoint_count
                )
    result = runner.run_job(train_job)
    assert result.status == 'successful'
    results = result.results
    new_weights = results['weights']
    omega = results['omega']
    train_stats = results['train_stats']
    assert result.job.job_type is JobTypes.JOB_TRAIN.name
    assert type(new_weights) == list
    assert type(new_weights[0]) == np.ndarray
    assert type(omega) == int or type(omega) == float
    assert type(train_stats) == dict

def test_dmlrunner_validate_job_returns_stats( \
        runner, mnist_filepath, train_dmlresult_obj):
    job_results = train_dmlresult_obj
    session_filepath = job_results.job.session_filepath
    datapoint_count = job_results.job.datapoint_count
    result = train_dmlresult_obj
    assert result.status == 'successful'
    results = result.results
    new_weights = results['weights']
    validate_job = make_validate_job(
                    new_weights, 
                    session_filepath,
                    datapoint_count
                )
    validate_job.hyperparams['split'] = 1 - validate_job.hyperparams['split']
    result = runner.run_job(validate_job)
    assert result.status == 'successful'
    results = result.results
    val_stats = results['val_stats']
    assert result.job.job_type is JobTypes.JOB_VAL.name
    assert type(val_stats) == dict

def test_dmlrunner_initialize_job_weights_can_be_serialized(init_dmlresult_obj):
    initial_weights = init_dmlresult_obj.results['weights']
    same_weights = deserialize_weights(serialize_weights(initial_weights))
    assert all(np.allclose(arr1, arr2) for arr1,arr2 in zip(same_weights, initial_weights)) 

def test_dmlrunner_averaging_weights(runner, train_dmlresult_obj):
    initial_weights = train_dmlresult_obj.results['weights']
    assert initial_weights
    avg_job = DMLAverageJob(
        omega=train_dmlresult_obj.results['omega'],
        sigma_omega=train_dmlresult_obj.results['omega'],
        weights=initial_weights,
        new_weights=serialize_weights(initial_weights)
    )
    averaged_weights = runner._average(avg_job).results['weights']
    assert all(np.allclose(arr1, arr2) for arr1,arr2 in zip(averaged_weights, initial_weights))
