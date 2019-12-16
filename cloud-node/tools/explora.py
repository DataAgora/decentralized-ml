import sys
import asyncio

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

    async def start_new_session(self, repo_id, library_type, checkpoint_frequency=1):
        self.CLOUD_NODE_HOST = 'ws://' + repo_id + self.CLOUD_BASE_URL

        hyperparams = {
            "batch_size": 100,
            "epochs": 5,
            "shuffle": True,
        }

        h5_model_path = "assets/my_model.h5"

        upload_keras_model(repo_id, "test-session", h5_model_path)

        NEW_MESSAGE = {
            "type": "NEW_SESSION",
            "repo_id": repo_id,
            "hyperparams": hyperparams,
            "session_id": "test-session",
            "checkpoint_frequency": checkpoint_frequency,
            "selection_criteria": {
                "type": "ALL_NODES",
            },
            "continuation_criteria": {
                "type": "PERCENTAGE_AVERAGED",
                "value": 0.75
            },
            "termination_criteria": {
                "type": "MAX_ROUND",
                "value": 5
            },
            "library_type": library_type,
        }

        NEW_CONNECTION_MESSAGE = {
            "type": "REGISTER",
            "node_type": "dashboard",
        }

        await self._start_new_session(NEW_CONNECTION_MESSAGE, NEW_MESSAGE)


    async def _start_new_session(self, new_connection_message, new_message):
        num_reconnections = 3
        while True:
            try:
                async with websockets.connect(self.CLOUD_NODE_HOST, max_size=2**22) as websocket:
                    await websocket.send(json.dumps(new_connection_message))
                    await websocket.send(json.dumps(new_message))
                    response = await websocket.recv()
                    json_response = json.loads(response)
                    if json_response.get("action", None) == 'STOP':
                        print("Session complete! Check dashboard for final model!")
                    else:
                        print("Unknown response received:")
                        print(json_response)
                        print("Stopping...")
                    return
            except Exception as e:
                print(e)
                num_reconnections -= 1
                if not num_reconnections:
                    print("Failed to connect!")
                    return


