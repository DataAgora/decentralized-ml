import sys
import asyncio
import uuid

import json
import base64
import boto3
import keras

from s3_utils import upload_keras_model
import websockets


class Explora(object):
    """
    Communicate with given cloud node and initiate DML session
    """
    def __init__(self):
        #log.startLogging(sys.stdout)
        self.CLOUD_BASE_URL = ".au4c4pd2ch.us-west-1.elasticbeanstalk.com"

    async def start_new_session(self, repo_id, library_type, h5_model_path):
        self.CLOUD_NODE_HOST = 'ws://localhost'

        hyperparams = {
            "batch_size": 100,
            "epochs": 5,
            "shuffle": True,
        }
        
        session_id = str(uuid.uuid4())
        upload_keras_model(repo_id, session_id, h5_model_path)
        ios_config = {}

        if library_type == "IOS":
            ios_config = {
                "data_type": "image",
                "image_config": {
                    "dims": (28, 28),
                    "color_space": "GRAYSCALE",
                },
                "class_labels": [str(i) for i in range(10)]
            }

        

        NEW_MESSAGE = {
            "type": "NEW_SESSION",
            "repo_id": repo_id,
            "dataset_id": "mnist-sample",
            "hyperparams": hyperparams,
            "session_id": session_id,
            "checkpoint_frequency": 1,
            "selection_criteria": {
                "type": "ALL_NODES",
            },
            "continuation_criteria": {
                "type": "PERCENTAGE_AVERAGED",
                "value": 0.75
            },
            "termination_criteria": {
                "type": "MAX_ROUND",
                "value": 2
            },
            "library_type": library_type,
            "ios_config": ios_config,
            "is_demo": True,
        }

        NEW_CONNECTION_MESSAGE = {
            "type": "REGISTER",
            "node_type": "dashboard",
            "repo_id": repo_id,
            "api_key": "demo-api-key",
            "is_demo": True
        }

        await self._start_new_session(NEW_CONNECTION_MESSAGE, NEW_MESSAGE)


    async def _start_new_session(self, registration_message, new_session_message, \
            num_reconnections=3):
        try:
            async with websockets.connect(self.CLOUD_NODE_HOST, max_size=2**22) as websocket:
                print("Starting session!\nWaiting...")
                await websocket.send(json.dumps(registration_message))
                response = await websocket.recv()
                json_response = json.loads(response)
                if json_response.get("action", None) == 'REGISTRATION_SUCCESS':
                    print("Registration success!")
                    await websocket.send(json.dumps(new_session_message))
                    response = await websocket.recv()
                    json_response = json.loads(response)
                    if json_response.get("action", None) == 'STOP':
                        print("Session complete! Check dashboard for final model!")
                    elif json_response.get("error", None):
                        print("Received error!")
                        print(json_response["error_message"])
                        print("Stopping...") 
                    else:
                        print(json_response)
                    return
                elif json_response.get("error", None):
                            print("Received error!")
                            print(json_response["error_message"])
                            print("Stopping...") 
                else:
                    print(json_response)
        except Exception as e:
            print(e)
            num_reconnections -= 1
            if not num_reconnections:
                print("Failed to connect!")
                return
            self._start_new_session(registration_message, new_session_message, \
                num_reconnections=num_reconnections-1)


