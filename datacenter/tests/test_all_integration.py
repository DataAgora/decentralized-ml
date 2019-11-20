import tests.context
import pytest
import time
from multiprocessing import Process
import os
import shutil
import ipfsapi

from core.communication_manager         import CommunicationManager
from core.runner                        import DMLRunner
from core.scheduler                     import DMLScheduler
from core.configuration                 import ConfigurationManager
from tests.testing_utils                import make_initialize_job, make_serialized_job
from core.utils.enums                   import RawEventTypes, JobTypes, MessageEventTypes
from core.utils.keras                   import serialize_weights
from core.blockchain.blockchain_gateway import BlockchainGateway
from core.blockchain.blockchain_utils   import setter, TxEnum
from core.dataset_manager               import DatasetManager


@pytest.fixture(scope='session')
def config_manager():
    config_manager = ConfigurationManager()
    config_manager.bootstrap(
        config_filepath='tests/artifacts/integration/configuration.ini'
    )
    return config_manager

@pytest.fixture(scope='session')
def config_manager_two():
    config_manager = ConfigurationManager()
    config_manager.bootstrap(
        config_filepath='tests/artifacts/integration/configuration2.ini'
    )
    return config_manager

@pytest.fixture(scope='session')
def ipfs_client(config_manager):
    config = config_manager.get_config()
    return ipfsapi.connect(config.get('BLOCKCHAIN', 'host'), 
                            config.getint('BLOCKCHAIN', 'ipfs_port'))

@pytest.fixture(scope='session')
def mnist_uuid():
    return '0fcf9cbb-39df-4ad6-9042-a64c87fecfb3'

@pytest.fixture(scope='session')
def mnist_uuid_two():
    return 'd16c6e86-d103-4e71-8741-ee1f888d206c'

@pytest.fixture(scope='session')
def transformed_filepath():
    return 'tests/artifacts/integration/mnist'+'/transformed'

@pytest.fixture(scope='session', autouse=True)
def cleanup(transformed_filepath):
    # Will be executed before the first test
    yield
    # Will be executed after the last test
    if os.path.isdir(transformed_filepath):
        shutil.rmtree(transformed_filepath)

@pytest.fixture(scope='session')
def new_session_event(mnist_uuid, mnist_uuid_two):
    serialized_job = make_serialized_job()
    new_session_event = {
            "optimizer_params": {
                "num_averages_per_round": 1, 
                "max_rounds": 2,
                "optimizer_type": "FEDERATED_AVERAGING"
            },
            "serialized_job": serialized_job,
            "participants": [mnist_uuid, mnist_uuid_two]
    }
    return new_session_event

@pytest.fixture(scope='session')
def new_session_key(mnist_uuid):
    return {"dataset_uuid": mnist_uuid, "label_column_name": "label"}

@pytest.fixture(scope='session')
def new_session_key_two(mnist_uuid_two):
    return {"dataset_uuid": mnist_uuid_two, "label_column_name": "label"}

@pytest.fixture(scope='session')
def dataset_manager(config_manager):
    dataset_manager = DatasetManager(config_manager)
    dataset_manager.bootstrap()
    return dataset_manager

def setup_client(config_manager, client):
    """
    Set up and return communication_manager, blockchain_gateway, scheduler
    """
    dataset_manager = DatasetManager(config_manager)
    dataset_manager.bootstrap()
    communication_manager = CommunicationManager()
    blockchain_gateway = BlockchainGateway()
    blockchain_gateway.configure(
        config_manager=config_manager,
        communication_manager=communication_manager,
        ipfs_client=client,
        dataset_manager=dataset_manager
    )
    scheduler = DMLScheduler(config_manager)
    scheduler.configure(
        communication_manager=communication_manager,
        ipfs_client=client,
        blockchain_gateway=blockchain_gateway
    )
    communication_manager.configure(
        scheduler=scheduler,
        dataset_manager=dataset_manager
    )
    return communication_manager, blockchain_gateway, scheduler

def test_federated_learning_two_clients_automated(new_session_event, new_session_key, new_session_key_two, 
    config_manager_two, config_manager, ipfs_client):
    """
    Tests fully automated federated learning.
    """
    # Set up first client
    communication_manager, blockchain_gateway, scheduler = setup_client(config_manager, ipfs_client)
    # Set up second client
    communication_manager_2, blockchain_gateway_2, scheduler_2 = setup_client(config_manager_two, ipfs_client)
    # (0) Someone sends decentralized learning event to the chain
    tx_receipt = setter(
        client=blockchain_gateway._client,
        key=new_session_key, 
        port=blockchain_gateway._port,
        value=new_session_event, 
        flag=True,
        round_num=0
    )
    tx_receipt_two = setter(
        client=blockchain_gateway._client,
        key=new_session_key_two, 
        port=blockchain_gateway._port,
        value=new_session_event, 
        flag=True,
        round_num=0
    )
    assert tx_receipt
    assert tx_receipt_two
    scheduler.start_cron(period_in_mins=0.01)
    scheduler_2.start_cron(period_in_mins=0.01)
    blockchain_gateway.start_cron(period_in_mins=0.01)
    blockchain_gateway_2.start_cron(period_in_mins=0.01)
    timeout = 50 + time.time()
    while time.time() < timeout and (len(scheduler.processed) != 8 or len(scheduler_2.processed) != 8):
        time.sleep(1)
    scheduler.stop_cron()
    scheduler_2.stop_cron()
    blockchain_gateway.stop_cron()
    blockchain_gateway_2.stop_cron()
    assert len(scheduler.processed) == 8, \
        "Jobs {} failed/not completed in time!".format([
        result.job.job_type for result in scheduler.processed])  
    assert len(scheduler_2.processed) == 8, \
        "Jobs {} failed/not completed in time!".format([
        result.job.job_type for result in scheduler_2.processed])    
    assert communication_manager.optimizer is None
    assert communication_manager_2.optimizer is None

def test_federated_learning_two_clients_manual(new_session_event, new_session_key, new_session_key_two, 
    config_manager_two, config_manager, ipfs_client):    
    """
    Integration test that checks that one round of federated learning can be
    COMPLETED with max_rounds = 2, num_averages_per_round = 2

    This is everything that happens in this test:

    """
    # Set up first client
    communication_manager, blockchain_gateway, scheduler = setup_client(config_manager, ipfs_client)
    # Set up second client
    communication_manager_2, blockchain_gateway_2, scheduler_2 = setup_client(config_manager_two, ipfs_client)
    # (0) Someone sends decentralized learning event to the chain
    tx_receipt = setter(
        client=blockchain_gateway._client,
        key=new_session_key, 
        port=blockchain_gateway._port,
        value=new_session_event, 
        flag=True,
        round_num=0
    )
    tx_receipt_two = setter(
        client=blockchain_gateway._client,
        key=new_session_key_two, 
        port=blockchain_gateway._port,
        value=new_session_event, 
        flag=True,
        round_num=0
    )
    assert tx_receipt
    assert tx_receipt_two
    # (1) Gateway_1 listens for the event
    blockchain_gateway._listen(blockchain_gateway._handle_new_session_creation, 
        blockchain_gateway._filter_new_session)
    # (2) Gateway_2 listens for the event
    blockchain_gateway_2._listen(blockchain_gateway_2._handle_new_session_creation, 
        blockchain_gateway_2._filter_new_session)
    # (3) Scheduler_1 and Scheduler_2 runs the following jobs:
        # (3a.1) JOB_INIT
        # (3a.2) JOB_SPLIT
        # (3b) JOB_TRAIN
        # (3c) JOB_COMM
    scheduler.start_cron(period_in_mins = 0.01)
    scheduler_2.start_cron(period_in_mins=0.01)
    timeout = time.time() + 25
    while time.time() < timeout and (len(scheduler.processed) != 4\
        or len(scheduler_2.processed) != 4):
        time.sleep(5)
    assert len(scheduler.processed) == 4, "Jobs failed/not completed in time!"
    assert len(scheduler_2.processed) == 4, "Jobs failed/not completed in time!"
    # (4) Gateway_1 listens for the new weights and hears only Gateway_2's weights
    blockchain_gateway._listen(blockchain_gateway._handle_new_session_info,
        blockchain_gateway._filter_new_session_info)
    # (6) Gateway_2 listens for the new weights and hears only Gateway_1's weights
    blockchain_gateway_2._listen(blockchain_gateway_2._handle_new_session_info,
        blockchain_gateway_2._filter_new_session_info)
    # (8) Scheduler_1 and Scheduler_2 runs the following jobs:
        # (6a) JOB_AVG
        # (6a) JOB_TRAIN
        # (6a) JOB_COMM
    timeout = time.time() + 20
    while time.time() < timeout and (len(scheduler.processed) != 7\
        or len(scheduler_2.processed) != 7):
        time.sleep(4)
    assert len(scheduler.processed) == 7, \
        "Jobs {} failed/not completed in time!".format([
            result.job.job_type for result in scheduler.processed])
    assert len(scheduler_2.processed) == 7, "Jobs failed/not completed in time!"
    # (4) Gateway_1 listens for the new weights and hears only Gateway_2's weights
    blockchain_gateway._listen(blockchain_gateway._handle_new_session_info,
        blockchain_gateway._filter_new_session_info)
    # (6) Gateway_2 listens for the new weights and hears only Gateway_1's weights
    blockchain_gateway_2._listen(blockchain_gateway_2._handle_new_session_info,
        blockchain_gateway_2._filter_new_session_info)
    # (13) Optimizer tells Communication Manager to schedule JOB_AVG
    # (14) Scheduler_1 and Scheduler_2 runs the following jobs:
        # (9a) JOB_AVG
    timeout = time.time() + 10
    while time.time() < timeout and (len(scheduler.processed) != 8\
        or len(scheduler_2.processed) != 8):
        time.sleep(2)
    scheduler.stop_cron()
    scheduler_2.stop_cron()
    blockchain_gateway.reset()
    blockchain_gateway_2.reset()
    assert len(scheduler.processed) == 8, "Jobs failed/not completed in time!"
    assert len(scheduler_2.processed) == 8, "Jobs failed/not completed in time!"
    # (10) Optimizer terminates
    assert communication_manager.optimizer is None, "Should have terminated!"
    assert communication_manager_2.optimizer is None, "Should have terminated!"
    # and that completes one local round of federated learning!

def test_communication_manager_integration(new_session_event, new_session_key, config_manager, ipfs_client, dataset_manager):
    """
    Integration test that checks that the Communication Manager can initialize,
    train, (and soon communicate) a model, and average a model.
    This is everything that happens in this test:

    (1) Communication Manager receives the packet it's going to receive from BlockchainGateway
    (2) Communication Manager gives packet to Optimizer
    (3) Optimizer tells Communication Manager to schedule an initialization job
    (4) Communication Manager schedules initialization job
    (5) Communication Manager receives DMLResult for initialization job from Scheduler
    (6) Communication Manager gives DMLResult to Optimizer
    (7) Optimizer updates its weights to initialized model
    (8) Optimizer tells Communication Manager to schedule a training job
    (9) Communication Manager schedules training job
    (10) Communication Manager receives DMLResult for training job from Scheduler
    (11) Communication Manager gives DMLResult to Optimizer
    (12) Optimizer updates its weights to trained weights
    (13) Optimizer tells Communication Manager to schedule a communication job
    (14) Communication Manager schedules communication job
    (15) Communication Manager receives DMLResult for communication job from Scheduler
    (16) Communication Manager gives DMLResult to Optimizer
    (17) Optimizer tells the Communication Manager to do nothing
    (18) Communication Manager receives new weights from Blockchain Gateway
    (19) Communication Manager gives new weights to Optimizer
    (20) Optimizer tells Communication Manager to schedule an averaging job
    (21) Communication Manager schedules averaging job
    (22) Communication Manager receives DMLResult for averaging job from Scheduler
    (23) Communication Manager gives DMLResult to Optimizer
    (24) Optimizer updates its weights to initialized model and increments num_averages_per_round
    (25) Optimizer tells Communication Manager to do nothing
    (26) Communication Manager receives new weights from Blockchain Gateway
    (27) Communication Manager gives new weights to Optimizer
    (28) Optimizer tells Communication Manager to schedule an averaging job
    (29) Communication Manager schedules averaging job
    (30) Communication Manager receives DMLResult for averaging job from Scheduler
    (31) Communication Manager gives DMLResult to Optimizer
    (32) Optimizer updates its weights to initialized model and increments num_averages_per_round
    (33) Optimizer tells Communication Manager to schedule a training job since it's heard enough

    NOTE: Timeout errors can be as a result of Runners repeatedly erroring. Check logs for this.
    """
    communication_manager, blockchain_gateway, scheduler = setup_client(
        config_manager, ipfs_client)
    nested_dict = {
        TxEnum.KEY.name: new_session_key,
        TxEnum.CONTENT.name: new_session_event
    }
    args = {
        TxEnum.KEY.name: MessageEventTypes.NEW_SESSION.name,
        TxEnum.CONTENT.name: nested_dict
    }
    communication_manager.inform(
        RawEventTypes.NEW_MESSAGE.name,
        args
    )
    # assert communication_manager.optimizer.job.job_type == JobTypes.JOB_INIT.name or \
    #     communication_manager.optimizer.job.job_type == JobTypes.JOB_SPLIT.name, \
    #     "Should be ready to init or transform_split!"
    timeout = time.time() + 3
    while time.time() < timeout and len(scheduler.processed) == 0:
        # initialization job
        scheduler.runners_run_next_jobs()
        time.sleep(0.1)
    assert len(scheduler.processed) == 2, "Initialization failed/not completed in time!"
    timeout = time.time () + 3
    # assert communication_manager.optimizer.job.job_type == JobTypes.JOB_TRAIN.name, \
    #     "Should be ready to train!"
    timeout = time.time() + 3
    while time.time() < timeout and len(scheduler.processed) == 2:
        # training job
        scheduler.runners_run_next_jobs()
        time.sleep(0.1)
    assert len(scheduler.processed) == 3, "Training failed/not completed in time!"
    # assert communication_manager.optimizer.job.job_type == JobTypes.JOB_COMM.name, \
    #     "Should be ready to communicate!"
    timeout = time.time() + 3
    while time.time() < timeout and len(scheduler.processed) == 3:
        # communication job
        scheduler.runners_run_next_jobs()
        time.sleep(0.1)
    assert len(scheduler.processed) == 4, "Communication failed/not completed in time!"
    # now the communication manager should be idle
    scheduler.runners_run_next_jobs()
    time.sleep(0.1)
    assert len(scheduler.processed) == 4, "No job should have been run!"
    # now it should hear some new weights
    new_weights_event = {
        TxEnum.KEY.name: MessageEventTypes.NEW_WEIGHTS.name,
        TxEnum.CONTENT.name: scheduler.processed[3].job.serialize_job()
    }
    communication_manager.inform(
        RawEventTypes.NEW_MESSAGE.name,
        new_weights_event
    )
    # assert communication_manager.optimizer.job.job_type == JobTypes.JOB_AVG.name, \
    #     "Should be ready to average!"
    timeout = time.time() + 3
    while time.time() < timeout and len(scheduler.processed) == 4:
        # averaging job
        scheduler.runners_run_next_jobs()
        time.sleep(0.1)
    assert len(scheduler.processed) == 5, "Averaging failed/not completed in time!"
    assert communication_manager.optimizer.curr_averages_this_round == 0, \
        "Either did not hear anything, or heard too much!"
    # now we should be ready to train
    # assert communication_manager.optimizer.job.job_type == JobTypes.JOB_TRAIN.name, \
    #     "Should be ready to train!"
    scheduler.reset()
    # and that completes one local round of federated learning!
