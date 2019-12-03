import uuid
import logging

import state
import copy
from model import convert_keras_model, fetch_keras_model
from message import LibraryType


logging.basicConfig(level=logging.DEBUG)

def start_new_session(message, clients):
    """
    Starts a new DML session.

    Args:
        message (NEW_SESSION): The `NEW_SESSION` message sent to the server.
        clients (list): List of `LIBRARY` clients to train with.

    Returns:
        dict: Returns a dictionary detailing whether an error occurred and
            if there was no error, what the next action is.
    """
    print("Starting new session...")

    # 1. If server is BUSY or library type is not recognized, error. 
    #    Otherwise, mark the service as BUSY.
    if state.state["busy"]:
        print("Aborting because the server is busy.")
        return {
            "error": True,
            "message": "Server is already busy working."
        }
    elif message.library_type not in \
            (LibraryType.PYTHON.value, LibraryType.JS.value):
        return {
            "error": True,
            "message": "Invalid library type!"
        }

    state.state_lock.acquire()
    state.state["busy"] = True

    # 2. Set the internal round variable to 1, reset the number of nodes
    #    averaged to 0, update the initial message.
    state.state["current_round"] = 1
    state.state["num_nodes_averaged"] = 0
    state.state["initial_message"] = message
    state.state["repo_id"] = message.repo_id
    state.state["session_id"] = message.session_id
    state.state["checkpoint_frequency"] = message.checkpoint_frequency

    # 3. According to the 'Selection Criteria', choose clients to forward
    #    training messages to.
    chosen_clients = _choose_clients(
        message.selection_criteria,
        clients_dict["LIBRARY"]
    )
    state.state["num_nodes_chosen"] = len(chosen_clients)

    new_message = {
        "session_id": state.state["session_id"],
        "repo_id": state.state["repo_id"],
        "round": 1,
        "action": "TRAIN",
        "hyperparams": message.hyperparams,
    }

    # 4. Record the message to be sent and the library type we are training
    #    with. By default, we use gradients for transmission.
    state.state["last_message_sent_to_library"] = new_message
    state.state["library_type"] = message.library_type
    state.state["use_gradients"] = True

    # 5. Retrieve the initial model we are training with.
    fetch_keras_model()

    # 6. If we are training with a JAVASCRIPT library, convert the model to 
    #    TFJS and host it on the server.
    if state.state["library_type"] == LibraryType.JS.value:
        _ = convert_keras_model()    
        state.state["use_gradients"] = False

    # 7. Kickstart a DML Session with the model and round # 1
    state.state_lock.release()
    return {
        "error": False,
        "action": "BROADCAST",
        "client_list": chosen_clients,
        "message": new_message,
    }


def start_next_round(clients):
    """
    Starts a new round in the current DML Session.

    Args:
        message (dict): The `NEW_SESSION` message sent to the server.
        clients (list): List of `LIBRARY` clients to train with.

    Returns:
        dict: Returns a dictionary detailing whether an error occurred and
            if there was no error, what the next action is.
    """
    print("Starting next round...")
    state.state["num_nodes_averaged"] = 0

    message = state.state["initial_message"]

    # According to the 'Selection Criteria', choose clients to forward
    # training messages to.
    chosen_clients = _choose_clients(message.selection_criteria, clients)
    state.state["num_nodes_chosen"] = len(chosen_clients)

    new_message = {
        "session_id": state.state["session_id"],
        "repo_id": state.state["repo_id"],
        "round": state.state["current_round"],
        "action": "TRAIN",
        "hyperparams": message.hyperparams,
    }
    state.state["last_message_sent_to_library"] = new_message
    # Swap weights and convert (NEW) .h5 model into TFJS model
    assert state.state["current_round"] > 0

    if state.state['library_type'] == LibraryType.PYTHON.value:
        new_message['gradients'] = [gradient.tolist() for gradient in state.state['current_gradients']]
    else:
        _ = convert_and_save_model(state.state["current_round"] - 1)

    # Kickstart a DML Session with the TFJS model
    
    return {
        "error": False,
        "action": "BROADCAST",
        "client_list": chosen_clients,
        "message": new_message,
    }

def _choose_clients(selection_criteria, client_list):
    """
    TO BE FINISHED.

    Need to define a selection criteria object first.

    Right now it just chooses all clients.
    """
    return client_list
