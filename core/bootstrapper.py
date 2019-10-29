import threading
import asyncio

from core.configuration import ConfigurationManager
from core.websocket_utils import WebSocketClient
from core.runner import DMLRunner
from core.fed_avg_optimizer import FederatedAveragingOptimizer

import logging

logging.basicConfig(format='[%(name)s] %(asctime)s %(levelname)s %(message)s',
                        level=logging.INFO)


def bootstrap(repo_id=None):
    """
    Bootstraps the data provider unix service.

    It instantiates the Configuration Manager, Dataset Manager, Communication
    Manager and the Execution Pipeline.
    """
    # 1. Set up Configuration Manager.
    config_manager = ConfigurationManager()
    config_manager.bootstrap()

    # # # 2. Set up Dataset Manager.
    # dataset_manager = DatasetManager(
    #     config_manager=config_manager
    # )
    # dataset_manager.bootstrap()

    # 3. Set up the Communication Manager.

    runner = DMLRunner(config_manager)

    optimizer = FederatedAveragingOptimizer(runner)

    # blockchain_gateway = BlockchainGateway()

    # # 4. Set up the Execution Pipeline (Scheduler, Runners)
    # # and run the Scheduler's cron on a new thread.
    # scheduler = DMLScheduler(
    #     config_manager=config_manager,
    # )
    # scheduler.configure(
    #     communication_manager=communication_manager
    # )
    # t1 = threading.Thread(
    #     target=scheduler.start_cron,
    #     args=(0.05,),
    #     daemon=False,
    # )
    # t1.start()

    loop = asyncio.get_event_loop()

    websocket_client = WebSocketClient(optimizer, config_manager, repo_id)
    # mappings = dataset_manager.get_mappings()


    # 7. Wait for the threads to end.
    # TODO: Need to make it work as a daemon.
    loop.run_until_complete(websocket_client.prepare_dml())

    
