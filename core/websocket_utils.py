import asyncio
import websockets
import json
import threading
import logging

from core.utils.enums import RawEventTypes, MessageEventTypes

# logging.basicConfig(level=logging.DEBUG,
# 					format='[WebSocketClient] %(asctime)s %(levelname)s %(message)s')
from functools import singledispatch


@singledispatch
def to_serializable(val):
    """Used by default."""
    return str(val)

busy = False

class WebSocketClient(object):

    def __init__(self, optimizer, config_manager, repo_id):
        self._optimizer = optimizer
        self.repo_id = repo_id
        self._websocket_url = url = "ws://" + repo_id + ".au4c4pd2ch.us-west-1.elasticbeanstalk.com"
        self.reconnections_remaining = 3
        self.logger = logging.getLogger("WebSocketClient")
        self.logger.info("WebSocketClient {} set up!".format(repo_id))

    async def prepare_dml(self):
        stop_received = False
        self.reconnections_remaining -= 1
        while not stop_received:
            if not self.reconnections_remaining:
                self.logger.info("Failed to connect!")
                return
            async with websockets.connect(self._websocket_url, max_size=2**22) as websocket:
                await self.send_register_message(websocket)
                while True:
                    json_response = await self.listen(websocket)
                    if not json_response["success"]:
                        break
                    self.reconnections_remaining = 3
                    assert 'action' in json_response, 'No action found: {}'.format(str(json_response))
                    if json_response['action'] == 'TRAIN':
                        self.logger.info('Received TRAIN message, beginning training...')
                        results = self._optimizer.received_new_message(json_response)
                        if not results["success"]:
                            break
                        await self.send_new_weights(websocket, results, json_response['session_id'], json_response['round'])
                    elif json_response['action'] == 'STOP':
                        self.logger.info('Received STOP message, terminating...')
                        stop_received = True
                        break
                    else:
                        self.logger.info('Unknown action [{}] received, ignoring...'.format(json_response['action']))

    async def send_register_message(self, websocket): 
        registration_message = {
            "type": "REGISTER",
            "node_type": "LIBRARY"
        }
        self.logger.info("Sending register message for {}".format(self.repo_id))
        await websocket.send(json.dumps(registration_message))


    async def send_new_weights(self, websocket, results, session_id, round):
        new_weights_message = {
            "type": "NEW_WEIGHTS",
            "session_id": session_id,
            "action": "TRAIN",
            "results": results,
            "round": round
        }
        self.logger.info("Sending new weights for {}".format(self.repo_id))
        await websocket.send(json.dumps(new_weights_message, default=to_serializable))
            

    async def listen(self, websocket):
        try:
            response = await websocket.recv()
        except websockets.exceptions.ConnectionClosedError as e:
            print(str(e))
            self.logger.info("Disconnection occurred, reconnecting...")
            return {"success": False}
            
        self.logger.info("Received message for {}!".format(self.repo_id))
        #self.logger.info("Message is: {}".format(response))
        json_response = json.loads(response)
        json_response["success"] = True
        return json_response


    
