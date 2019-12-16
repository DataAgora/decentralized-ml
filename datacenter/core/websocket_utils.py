import asyncio
import websockets
import json
import threading
import logging
import requests
import urllib.request
import os

from core.utils.enums import RawEventTypes, MessageEventTypes
from websockets.client import WebSocketClientProtocol

from functools import singledispatch


@singledispatch
def to_serializable(val):
    """Used by default."""
    return str(val)

busy = False

class ClientWebSocketProtocol(WebSocketClientProtocol):
    def onPing():
        print("Ping received from {}".format(self.peer))
        self.sendPong(payload)
        print("Pong sent to {}".format(self.peer))

class WebSocketClient(object):
    def __init__(self, optimizer, config_manager, repo_id, test):
        self._optimizer = optimizer
        self.repo_id = repo_id
        base_url = "ws://{}.au4c4pd2ch.us-west-1.elasticbeanstalk.com"
        base_cloud = "http://{}.au4c4pd2ch.us-west-1.elasticbeanstalk.com"
        self._websocket_url = "ws://localhost:8999" if test else base_url.format(repo_id)
        self._cloud_url = "http://localhost:8999" if test else base_cloud.format(repo_id)
        self.reconnections_remaining = 3
        self.logger = logging.getLogger("WebSocketClient")
        self.logger.info("WebSocketClient {} set up!".format(repo_id))
        self.message_to_send = None

    async def prepare_dml(self):
        stop_received = False
        self.reconnections_remaining -= 1
        while not stop_received:
            if not self.reconnections_remaining:
                self.logger.info("Failed to connect!")
                return
            async with websockets.connect(self._websocket_url, ping_interval=None, \
                    ping_timeout=None, close_timeout=None, max_size=None, \
                    max_queue=None, read_limit=100000, write_limit=10000, \
                    create_protocol=ClientWebSocketProtocol) as websocket:
                await self.send_register_message(websocket)
                while True:
                    json_response = await self.listen(websocket)
                    if not json_response["success"]:
                        break
                    assert 'action' in json_response, 'No action found: {}'.format(str(json_response))
                    if json_response['action'] == 'TRAIN':
                        self.logger.info('Received TRAIN message, beginning training...')
                        url = self._cloud_url + "/model.h5"
                        if json_response["round"] == 1:
                            h5_model_folder = os.path.join('sessions', json_response['session_id'])
                            h5_model_filepath = os.path.join(h5_model_folder, 'model.h5')
                            if not os.path.isdir(h5_model_folder):
                                os.makedirs(h5_model_folder)
                            urllib.request.urlretrieve(url, h5_model_filepath)
                        results = self._optimizer.received_new_message(json_response)
                        if not results["success"]:
                            break
                        await self.send_new_weights(websocket, results, json_response['session_id'], json_response['round'])
                        self.reconnections_remaining = 3
                    elif json_response['action'] == 'STOP':
                        self.logger.info('Received STOP message, terminating...')
                        stop_received = True
                        self._optimizer.clear_session()
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
            "type": "NEW_UPDATE",
            "session_id": session_id,
            "action": "TRAIN",
            "results": results,
            "round": round,
        }
        self.logger.info("Sending new weights for {}".format(self.repo_id))
        try:
            await websocket.send(json.dumps(new_weights_message, default=to_serializable))
        except Exception as e:
            print("Error sending weights!: " + str(e))            
            return {"success": False}          

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


    
