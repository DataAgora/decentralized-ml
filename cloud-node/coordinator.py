import uuid
import logging

import state
import copy
from model import convert_keras_model_to_tfjs, fetch_keras_model, convert_keras_model_to_mlmodel
from message import LibraryType


logging.basicConfig(level=logging.ERROR)

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

    state.state["busy"] = True

    # 2. Set the internal round variable to 1, reset the number of nodes
    #    averaged to 0, update the initial message.
    state.state["current_round"] = 1
    state.state["num_nodes_averaged"] = 0
    state.state["initial_message"] = message
    state.state["repo_id"] = message.repo_id
    state.state["dataset_id"] = message.dataset_id
    state.state["session_id"] = message.session_id
    state.state["checkpoint_frequency"] = message.checkpoint_frequency
    state.state["ios_config"] = message.ios_config

    # 3. According to the 'Selection Criteria', choose clients to forward
    #    training messages to.
    chosen_clients = _choose_clients(message.selection_criteria, clients)
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

    # 6. If we are training with a JAVASCRIPT or IOS library, convert the model to 
    #    accordingly and host it on the server.
    if state.state["library_type"] == LibraryType.JS.value:
        _ = convert_keras_model_to_tfjs()    
        state.state["use_gradients"] = False
    elif state.state["library_type"] == LibraryType.IOS.value:
        data_type = state.state["ios_config"]["data_type"]
        state.state["library_type"] = LibraryType.IOS_IMAGE.value \
            if data_type == "image" else LibraryType.IOS_TEXT.value
        if state.state["library_type"] == LibraryType.IOS_IMAGE.value:
            state.state["hyperparams"] = message.hyperparams
            _ = convert_keras_model_to_mlmodel()
        new_message["dataset_id"] = state.state["dataset_id"]

    # 7. Kickstart a DML Session with the model and round # 1
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

    if state.state['library_type'] == LibraryType.PYTHON.value:
        new_message['gradients'] = [gradient.tolist() for gradient in state.state['current_gradients']]
    elif state.state['library_type'] == LibraryType.JS.value:
        _ = convert_keras_model_to_tfjs()
    elif state.state["library_type"] == LibraryType.IOS_IMAGE.value:
        _ = convert_keras_model_to_mlmodel()
        new_message["dataset_id"] = state.state["dataset_id"]
    elif state.state["library_type"] == LibraryType.IOS_TEXT.value:
        new_message["dataset_id"] = state.state["dataset_id"]
        
    state.state["last_message_sent_to_library"] = new_message
    assert state.state["current_round"] > 0

    return {
        "error": False,
        "action": "BROADCAST",
        "client_list": chosen_clients,
        "message": new_message,
    }

def stop_session(clients_dict):
    """
    Stop the current session. Reset state and return broadcast `STOP` message
    to all clients.

    Args:
        clients_dict (dict): Dictionary of clients, keyed by type of client
            (either `LIBRARY` or `DASHBOARD`).

    Returns:
        dict: Returns the broadcast message with action `STOP`.
    """
    state.reset_state()

    new_message = {
        "action": "STOP",
        "session_id": state.state["session_id"],
        "dataset_id": state.state["dataset_id"],
        "repo_id": state.state["repo_id"]
    }
    
    results = {
        "error": False,
        "action": "BROADCAST",
        "client_list": clients_dict["LIBRARY"] + clients_dict["DASHBOARD"],
        "message": new_message,
    }

    return results

def _choose_clients(selection_criteria, client_list):
    """
    TO BE FINISHED.

    Need to define a selection criteria object first.

    Right now it just chooses all clients.
    """
    return client_list
