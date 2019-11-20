import json
import socket

from websockets import connect


CLOUD_BASE_URL = ".au4c4pd2ch.us-west-1.elasticbeanstalk.com"

NEW_CONNECTION_MESSAGE = {
    "type": "REGISTER",
    "node_type": "dashboard",
}

async def connect(self, cloud_node_host, new_message, max_size=2**22, \
        num_reconnections=3):
    """
    Connect to server, register and start new session.
    Args:
        cloud_node_host (str): Server to connect to.
        new_message (dict): New session message to be sent to server.
        max_size (int): Maximum size in bytes for websocket transmission.
        num_reconnections (int): Number of consecutive reconnections allowed
            for some arbitrary failure to connect. 
    """
    while True:
        try:
            async with connect(cloud_node_host, max_size=2**22) as websocket:
                print("Starting session!\nWaiting...")
                await websocket.send(json.dumps(NEW_CONNECTION_MESSAGE))
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
        except socket.gaierror as e:
            print("Server not found!")
        except:
            num_reconnections -= 1
            if not num_reconnections:
                print("Failed to connect!")
                return