import tests.context

import time
import logging
import os
import pytest
import numpy as np
import ipfsapi

from core.scheduler                     import DMLScheduler
from core.configuration                 import ConfigurationManager
from core.blockchain.blockchain_gateway import BlockchainGateway
from core.communication_manager         import CommunicationManager
from core.dataset_manager               import DatasetManager
from tests.testing_utils                import (make_initialize_job, make_split_job, \
                                                make_communicate_job)

@pytest.fixture(scope='session')
def config_manager():
    config_manager = ConfigurationManager()
    config_manager.bootstrap(
        config_filepath='tests/artifacts/runner_scheduler/configuration.ini'
    )
    return config_manager

@pytest.fixture(scope='session')
def ipfs_client(config_manager):
    config = config_manager.get_config()
    ipfs_client = ipfsapi.connect(config.get('BLOCKCHAIN', 'host'), 
                            config.getint('BLOCKCHAIN', 'ipfs_port'))
    return ipfs_client


@pytest.fixture(scope='session')
def mnist_filepath():
    return 'tests/artifacts/runner_scheduler/mnist'

class MockCommunicationManager:
    def inform(self, dummy1, dummy2):
        pass
    def configure(self, scheduler, dataset_manager):
        pass

@pytest.fixture(scope='session')
def communication_manager():
    communication_manager = MockCommunicationManager()
    return communication_manager

@pytest.fixture(scope='session')
def blockchain_gateway(config_manager, ipfs_client, communication_manager, dataset_manager):
    blockchain_gateway = BlockchainGateway()
    blockchain_gateway.configure(config_manager, communication_manager, ipfs_client, dataset_manager)
    return blockchain_gateway

@pytest.fixture(scope='session')
def dataset_manager(config_manager):
    dataset_manager = DatasetManager(config_manager)
    dataset_manager.bootstrap()
    return dataset_manager
# NOTE: This is scope=function and not scope=session because of multiprocessing.
# If it's scope=session, tests will get interrupted by each other and then the assertions
# will fail because more jobs will be processed than they expected.
@pytest.fixture
def scheduler(config_manager, ipfs_client, communication_manager, dataset_manager, blockchain_gateway):
    scheduler = DMLScheduler(config_manager)
    scheduler.configure(communication_manager, ipfs_client, blockchain_gateway)
    communication_manager.configure(scheduler, dataset_manager)
    return scheduler

def test_dmlscheduler_communicate_single(scheduler, blockchain_gateway):
    # gateway should know the current state, which should be nothing
    assert type(blockchain_gateway.state) is not list
    assert len(blockchain_gateway.state) == 0
    # now we'll setter and hopefully append to the gateway's state
    communicate_job = make_communicate_job("testkey", "testweights")
    scheduler.add_job(communicate_job)
    scheduler.runners_run_next_jobs()
    timeout = time.time() + 3
    while time.time() < timeout and not scheduler.processed:
        time.sleep(0.1)
        scheduler.runners_run_next_jobs()
    # in the first place, we need to know that we actually communicated something
    assert len(scheduler.processed) == 1
    # now we check whether we were able to append to the gateway's state
    assert len(blockchain_gateway.state) == 1

def test_dmlscheduler_sanity(scheduler):
    """
    Check that the scheduling/running functionality is maintained.
    """
    initialize_job = make_initialize_job()
    scheduler.add_job(initialize_job)
    scheduler.runners_run_next_jobs()
    while not scheduler.processed:
        time.sleep(0.1)
        scheduler.runners_run_next_jobs()
    output = scheduler.processed.pop(0)
    initial_weights = output.results['weights']
    assert type(initial_weights) == list
    assert type(initial_weights[0]) == np.ndarray

def test_dmlscheduler_communicate(scheduler):
    """
    Test that the Scheduler can schedule/run Communicate Jobs.
    """
    m = 2
    for _ in range(m):
        communicate_job = make_communicate_job("testkey", "testweights")
        scheduler.add_job(communicate_job)
    scheduler.start_cron(period_in_mins=0.01)
    timeout = time.time() + 6
    while time.time() < timeout and len(scheduler.processed) < m:
        time.sleep(1)
    scheduler.stop_cron()
    assert len(scheduler.processed) == m, \
        "Jobs {} failed/not completed in time!".format([
        result.job.job_type for result in scheduler.processed])

def test_dmlscheduler_arbitrary_scheduling(scheduler):
    """
    Manually schedule events and check that all jobs are completed.
    """
    first = make_initialize_job()
    second = make_initialize_job()
    scheduler.add_job(first)
    scheduler.add_job(second)
    while len(scheduler.processed) == 0:
        scheduler.runners_run_next_jobs()
    third = make_initialize_job()
    fourth = make_initialize_job()
    scheduler.add_job(third)
    scheduler.add_job(fourth)
    while len(scheduler.processed) < 4:
        scheduler.runners_run_next_jobs()
    fifth = make_initialize_job()
    scheduler.add_job(fifth)
    while len(scheduler.processed) < 5:
        scheduler.runners_run_next_jobs()
    assert len(scheduler.processed) == 5, \
        "Jobs {} failed/not completed in time!".format([
        result.job.job_type for result in scheduler.processed])
    while scheduler.processed:
        output = scheduler.processed.pop(0)
        initial_weights = output.results['weights']
        assert type(initial_weights) == list
        assert type(initial_weights[0]) == np.ndarray

def test_dmlscheduler_cron(scheduler):
    """
    Test that the scheduler's cron works.
    """
    m = 2
    for _ in range(m):
        initialize_job = make_initialize_job()
        scheduler.add_job(initialize_job)
    scheduler.start_cron(period_in_mins = 0.01)
    timeout = time.time() + 6
    while time.time() < timeout and len(scheduler.processed) != m:
        time.sleep(1)
    scheduler.stop_cron()
    assert len(scheduler.processed) == m
    while scheduler.processed:
        output = scheduler.processed.pop(0)
        initial_weights = output.results['weights']
        assert type(initial_weights) == list
        assert type(initial_weights[0]) == np.ndarray
