import asyncio
import websockets
import json
import threading
import logging

from core.utils.enums import RawEventTypes, MessageEventTypes

logging.basicConfig(level=logging.DEBUG,
					format='[WebSocketClient] %(asctime)s %(levelname)s %(message)s')
from functools import singledispatch


@singledispatch
def to_serializable(val):
    """Used by default."""
    return str(val)

busy = False

class WebSocketClient(object):

    def __init__(self, optimizer, config_manager):
        repo_id = config_manager.get_config().get('GENERAL', 'repo_id')
        self._optimizer = optimizer
        self.repo_id = repo_id
        self._websocket_url = url = "ws://" + repo_id + ".au4c4pd2ch.us-west-1.elasticbeanstalk.com"
        self.consecutive_disconnections_allowed = 3
        logging.info("WebSocketClient {} set up!".format(repo_id))

    async def prepare_dml(self):
        stop_received = False
        self.consecutive_disconnections_allowed -= 1
        while not stop_received:
            async with websockets.connect(self._websocket_url, max_size=2**22) as websocket:
                await self.send_register_message(websocket)
                while True:
                    json_response = await self.listen(websocket)
                    if not json_response["success"]:
                        break
                    self.consecutive_disconnections_allowed = 3
                    assert 'action' in json_response, 'No action found: {}'.format(str(json_response))
                    if json_response['action'] == 'TRAIN':
                        logging.info('Received TRAIN message, beginning training...')
                        results = self._optimizer.received_new_message(json_response)
                        await self.send_new_weights(websocket, results, json_response['session_id'], json_response['round'])
                    elif json_response['action'] == 'STOP':
                        logging.info('Received STOP message, terminating...')
                        stop_received = True
                        break
                    else:
                        logging.info('Unknown action [{}] received, ignoring...'.format(json_response['action']))

    async def send_register_message(self, websocket): 
        registration_message = {
            "type": "REGISTER",
            "node_type": "LIBRARY"
        }
        logging.info("Sending register message for {}".format(self.repo_id))
        await websocket.send(json.dumps(registration_message))


    async def send_new_weights(self, websocket, results, session_id, round):
        new_weights_message = {
            "type": "NEW_WEIGHTS",
            "session_id": session_id,
            "action": "TRAIN",
            "results": results,
            "round": round
        }
        logging.info("Sending new weights for {}".format(self.repo_id))
        await websocket.send(json.dumps(new_weights_message, default=to_serializable))
            

    async def listen(self, websocket):
        try:
            response = await websocket.recv()
        except websockets.exceptions.ConnectionClosedError as e:
            logging.info("Disconnection occurred, reconnecting...")
            return {"success": False}
            
        logging.info("Received message for {}!".format(self.repo_id))
        #logging.info("Message is: {}".format(response))
        json_response = json.loads(response)
        json_response["success"] = True
        return json_response


    
