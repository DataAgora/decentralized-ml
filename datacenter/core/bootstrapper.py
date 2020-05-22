import threading
import asyncio
import tensorflow as tf
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

from core.configuration import ConfigurationManager
from core.websocket_utils import WebSocketClient
from core.runner import DMLRunner
from core.fed_avg_optimizer import FederatedAveragingOptimizer

import logging

logging.basicConfig(format='[%(name)s] %(asctime)s %(levelname)s %(message)s',
                        level=logging.INFO)


def bootstrap(repo_id="testRepo", api_key="demo-api-key", test=False):
    """
    Bootstraps the data provider unix service.

    It instantiates the Configuration Manager, Dataset Manager, Communication
    Manager and the Execution Pipeline.
    """
    # 1. Set up Configuration Manager.
    config_manager = ConfigurationManager()
    config_manager.bootstrap()

    runner = DMLRunner(config_manager)

    optimizer = FederatedAveragingOptimizer(runner, repo_id)

    loop = asyncio.get_event_loop()

    websocket_client = WebSocketClient(optimizer, config_manager, repo_id, api_key, test)
    # mappings = dataset_manager.get_mappings()


    # 7. Wait for the threads to end.
    # TODO: Need to make it work as a daemon.
    loop.run_until_complete(websocket_client.prepare_dml())

    
