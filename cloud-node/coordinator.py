import uuid
import logging

import state
import copy
from model import keras_to_tfjs, save_h5_model
from message.LibraryType import PYTHON, JS


logging.basicConfig(level=logging.DEBUG)

def start_new_session(message, clients):
    """
    Starts a new DML session.

    Args:
        message (dict): The `NEW_SESSION` message sent to the server.
        clients (list): List of `LIBRARY` clients.

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
    elif message.library_type not in (PYTHON.value, JS.value):
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
    state.state["session_id"] = str(uuid.uuid4())
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
    state.state["last_message_sent_to_library"] = new_message
    state.state["library_type"] = message.library_type
    save_h5_model(message.h5_model)
    # 4. Prepare message for sending.
    if state.state["library_type"] == PYTHON.value:
        # 4a. Save the model locally as an .h5 file, and add the model to
        #     the message.
        new_message = add_model_to_new_message(message.h5_model)
    else:
        # 4b. Convert the model to a TFJS model.
        _ = keras_to_tfjs()       

    # 5. Kickstart a DML Session with the model and round # 1
    state.state_lock.release()
    return {
        "error": False,
        "action": "BROADCAST",
        "client_list": chosen_clients,
        "message": new_message,
    }


def start_next_round(message, clients_list):
    """
    Starts a new round in the current DML Session.
    """
    print("Starting next round...")
    state.state["num_nodes_averaged"] = 0

    # According to the 'Selection Criteria', choose clients to forward
    # training messages to.
    chosen_clients = _choose_clients(message.selection_criteria, clients_list)
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
        if state.state["use_gradients"]:
            new_message['gradients'] = [gradient.tolist() for gradient in state.state['current_gradients']]
        else:
            new_message = add_model_to_new_message(new_message)
        new_message['use_gradients'] = state.state['use_gradients']
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

def _get_current_model():
    """
    Get current model (encoded)
    """
    h5_model_path = state.state["h5_model_path"]
    h5_model = get_encoded_h5_model(h5_model_path)
    return h5_model

def add_model_to_new_message():
    """
    Add model to Python message. Need to do a deep copy so that logs don't get flooded with h5_model.
    """
    copied_message = copy.deepcopy(state.state["last_message_sent_to_library"])
    copied_message["h5_model"] = _get_current_model()
    return copied_message
