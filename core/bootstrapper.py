import threading
import asyncio

from core.configuration import ConfigurationManager
from core.communication_manager import CommunicationManager
from core.scheduler import DMLScheduler
from core.dataset_manager import DatasetManager
from core.websocket_utils import WebSocketClient


def bootstrap():
    """
    Bootstraps the data provider unix service.

    It instantiates the Configuration Manager, Dataset Manager, Communication
    Manager and the Execution Pipeline.
    """
    # 1. Set up Configuration Manager.
    config_manager = ConfigurationManager()
    config_manager.bootstrap()

    # # 2. Set up Dataset Manager.
    dataset_manager = DatasetManager(
        config_manager=config_manager
    )
    dataset_manager.bootstrap()

    websocket_clients = {}

    # 3. Set up the Communication Manager.
    communication_manager = CommunicationManager()

    # blockchain_gateway = BlockchainGateway()

    # 4. Set up the Execution Pipeline (Scheduler, Runners)
    # and run the Scheduler's cron on a new thread.
    scheduler = DMLScheduler(
        config_manager=config_manager,
    )
    scheduler.configure(
        communication_manager=communication_manager
    )
    t1 = threading.Thread(
        target=scheduler.start_cron,
        args=(0.05,),
        daemon=False,
    )
    t1.start()

    thread_list = []

    mappings = dataset_manager.get_mappings()
    print(mappings)
    loop = asyncio.get_event_loop()
    websocket_clients["loop"] = loop
    for repo_id in mappings.keys():
        websocket_client = WebSocketClient(communication_manager, repo_id)
        websocket_clients[repo_id] = websocket_client
        t = threading.Thread(
            target=websocket_client.send_register_message,
            args=(loop,),
            daemon=False
        )
        thread_list.append(t)

    # 5. Configure the Communication Manager with the components it talks to.
    communication_manager.configure(
        scheduler=scheduler,
        dataset_manager=dataset_manager,
        websocket_clients=websocket_clients
    )

    [t.start() for t in thread_list]

    # 7. Wait for the threads to end.
    # TODO: Need to make it work as a daemon.
    t1.join()

    
