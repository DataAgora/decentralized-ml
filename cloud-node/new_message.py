import json
import os

import state
from message import Message
from message import MessageType
from coordinator import start_new_session, stop_session
from aggregator import handle_new_update, handle_no_dataset


def validate_new_message(payload):
    """
    Convert received message to JSON, classify the message, and sanity
    check received information.

    Args:
        payload (str): Received message.

    Returns:
        `Message`: Returns a `Message` object that holds the type of the new
            message along with all relevant information.
    """
    serialized_message = json.loads(payload)
    message = Message.make(serialized_message)
    print("Message ({0}) contents: {1}".format(message.type, message))
    return message

def _make_error_results(error_message, error_type):
    """
    Helper method to create error message dictionary.
    
    Args:
        error_message (str): The actual error message to send.
        error_type (str): The type of error that occurred.
    
    Returns:
        dict: The complete error message dictionary.
    """
    return {
        "action": "UNICAST",
        "message": {
            "type": error_type,
            "error": True, 
            "error_message": error_message
        }
    }

def process_new_message(message, factory, client):
    """
    Process the new message and take the correct action with the appropriate
    clients.

    Args:
        message (Message): `Message` object to process.
        factory (CloudNodeFactory): Factory that manages WebSocket clients.
    
    Returns:
        dict: Returns a dictionary detailing whether an error occurred and
            if there was no error, what the next action is.
    """
    results = {"action": None}

    if message.type == MessageType.REGISTER.value:
        # Register the node
        if message.node_type in ["DASHBOARD", "LIBRARY"]:
            if message.api_key != os.environ["API_KEY"]:
                return _make_error_results("API key provided is invalid!", \
                    "AUTHENTICATION")
            
            error_message = factory.register(client, message.node_type)
            if error_message:
                return _make_error_results(error_message, "REGISTRATION")
            
            print("Registered node as type: {}".format(message.node_type))

            if message.node_type == "LIBRARY" and state.state["busy"] is True:
                # There's a session active, we should incorporate the just
                # added node into the session!
                print("Adding the new library node to this round!")
                last_message = state.state["last_message_sent_to_library"]
                results["action"] = "UNICAST"
                results["message"] = last_message
        else:
            warning_message = "WARNING: Incorrect node type ({}) -- ignoring!"
            print(warning_message.format(message.node_type))

    elif message.type == MessageType.NEW_SESSION.value:
        # Verify this node has been registered
        if not factory.is_registered(client, message.node_type): 
            return _make_error_results("This client is not registered!", \
                "NOT_REGISTERED")

        # Start new DML Session
        if state.state["busy"]:
            print("Aborting because the server is busy.")
            return _make_error_results("Server is already busy working.", \
                "SERVER_BUSY") 
        results = start_new_session(message, factory.clients["LIBRARY"])

    elif message.type == MessageType.NEW_UPDATE.value:
        # Verify this node has been registered
        if not factory.is_registered(client, message.node_type): 
            return _make_error_results("This client is not registered!", \
                "NOT_REGISTERED")

        if factory.clients["DASHBOARD"]: 
            # Handle new weights (average, move to next round, terminate session)
            results = handle_new_update(message, factory.clients)
            print("Averaged new weights!")
        else:
            # Stopping session as the session starter has disconnected.
            results = stop_session(factory.clients)
            print("Disconnected from dashboard client, stopping session.")

    elif message.type == MessageType.NO_DATASET.value:
        # Verify this node has been registered
        if not factory.is_registered(client, message.node_type): 
            return _make_error_results("This client is not registered!", \
                "NOT_REGISTERED")

        if factory.clients["DASHBOARD"]: 
            # Handle `NO_DATASET` message (reduce # of chosen nodes, analyze 
            # continuation and termination criteria accordingly)
            results = handle_no_dataset(message, factory.clients)
            print("Handled `NO_DATASET` message!")
        else:
            # Stopping session as the session starter has disconnected.
            results = stop_session(factory.clients)
            print("Disconnected from dashboard client, stopping session.")

    else:
        print("Unknown message type!")
        return _make_error_results("Unknown message type!", "BAD_MESSAGE_TYPE")

    return results
