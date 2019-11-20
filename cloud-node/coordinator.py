import uuid
import logging

import state
from model import convert_and_save_b64model, convert_and_save_model, swap_weights


logging.basicConfig(level=logging.DEBUG)

def start_new_session(message, clients_dict):
    """
    Starts a new DML session.
    """
    print("Starting new session...")

    # // 1. If server is BUSY, error. Otherwise, mark the service as BUSY.
    if state.state["busy"]:
        print("Aborting because the server is busy.")
        return {
            "error": True,
            "message": "Server is already busy working."
        }
    state.state_lock.acquire()
    state.state["busy"] = True

    # // 2. Set the internal round variable to 1, reset the number of nodes
    # //    averaged to 0, update the initial message.
    state.state["current_round"] = 1
    state.state["num_nodes_averaged"] = 0
    state.state["initial_message"] = message
    state.state["repo_id"] = message.repo_id
    state.state["session_id"] = str(uuid.uuid4())

    # // 3. According to the 'Selection Criteria', choose clients to forward
    # //    training messages to.
    chosen_clients = _choose_clients(
        message.selection_criteria,
        clients_dict["LIBRARY"]
    )
    state.state["num_nodes_chosen"] = len(chosen_clients)

    # // 4. Convert .h5 model into TFJS model
    _ = convert_and_save_b64model(message.h5_model)

    # // 5. Kickstart a DML Session with the TFJS model and round # 1
    new_message = {
        "session_id": state.state["session_id"],
        "repo_id": state.state["repo_id"],
        "round": 1,
        "action": "TRAIN",
        "hyperparams": message.hyperparams,
    }
    state.state["last_message_sent_to_library"] = new_message
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

    # Swap weights and convert (NEW) .h5 model into TFJS model
    swap_weights()
    assert state.state["current_round"] > 0
    _ = convert_and_save_model(state.state["current_round"] - 1)

    # Kickstart a DML Session with the TFJS model
    new_message = {
        "session_id": state.state["session_id"],
        "repo_id": state.state["repo_id"],
        "round": state.state["current_round"],
        "action": "TRAIN",
        "hyperparams": message.hyperparams,
    }
    state.state["last_message_sent_to_library"] = new_message
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
