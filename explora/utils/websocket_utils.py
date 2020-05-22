import json
import socket

from websockets import connect


async def websocket_connect(websocket_url, registration_message, \
        new_session_message, max_size=2**22, num_reconnections=3):
    """
    Connect to server, register and start new session.

    Args:
        websocket_url (str): WebSocket to connect to.
        registration_message (dict): Registration message for server.
        new_session_message (dict): New session message to be sent to server
            after registration has succeeded.
        max_size (int): Maximum size in bytes for websocket transmission.
        num_reconnections (int): Number of consecutive reconnections allowed
            for some arbitrary failure to connect.
    """
    try:
        async with connect(websocket_url, max_size=2**22) as websocket:
            print("Starting session!")
            await websocket.send(json.dumps(registration_message))
            response = await websocket.recv()
            json_response = json.loads(response)
            if json_response.get("action", None) == 'REGISTRATION_SUCCESS':
                print("Registration success!\nWaiting...")
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
            elif json_response.get("error", None):
                print("Received error!")
                print(json_response["error_message"])
                print("Stopping...") 
            else:
                print(json_response)
    except socket.gaierror as e:
        print("Server not found!")
    except:
        num_reconnections -= 1
        if not num_reconnections:
            print("Failed to connect!")
            return
        websocket_connect(websocket_url, registration_message, \
            new_session_message, num_reconnections=num_reconnections-1)