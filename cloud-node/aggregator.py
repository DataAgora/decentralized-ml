import time
import logging

import numpy as np

import state
from updatestore import store_update
from coordinator import start_next_round, stop_session
from model import swap_weights, save_mlmodel_weights
from message import ClientType, LibraryType, ActionType, ErrorType, make_error_results


logging.basicConfig(level=logging.ERROR)

def handle_new_update(message, clients_dict):
    """
    Handle new weights from a Library.

    Args:
        message (NewUpdateMessage): The `NEW_UPDATE` message sent to the server.
        clients_dict (dict): Dictionary of clients, keyed by type of client
            (either `LIBRARY` or `DASHBOARD`).

    Returns:
        dict: Returns a dictionary detailing whether an error occurred and
            if there was no error, what the next action is.
    """
    results = {"action": ActionType.DO_NOTHING, "error": False}

    # 1. Check things match.
    if (state.state["library_type"] == LibraryType.IOS_IMAGE.value \
            or state.state["library_type"] == LibraryType.IOS_TEXT.value) \
            and state.state["dataset_id"] != message.dataset_id:
        error_message = "The dataset ID in the message doesn't match the service's."
        return make_error_results(error_message, ErrorType.NEW_UPDATE)

    if state.state["session_id"] != message.session_id:
        error_message = "The session ID in the message doesn't match the service's."
        return make_error_results(error_message, ErrorType.NEW_UPDATE)

    if state.state["current_round"] != message.round:
        error_message = "The round in the message doesn't match the current round."
        return make_error_results(error_message, ErrorType.NEW_UPDATE)

    state.state["last_message_time"] = time.time()

    # 2. Do running weighted average on the new weights.
    _do_running_weighted_average(message)

    # 3. Update the number of nodes averaged (+1)
    state.state["num_nodes_averaged"] += 1

    # 4. Save binary received weights, if received.
    # NOTE: This only used after the first round of training with IOS_TEXT.
    if message.binary_weights:
        save_mlmodel_weights(binary_weights)
    
    # 5. Swap in the newly averaged weights for this model.
    swap_weights()

    # 6. Store the model in S3, following checkpoint frequency constraints.
    if state.state["current_round"] % state.state["checkpoint_frequency"] == 0:
        store_update("ROUND_COMPLETED", message)

    # 7. If 'Continuation Criteria' is met...
    if check_continuation_criteria():
        # 7.a. Update round number (+1)
        state.state["current_round"] += 1

        # 7.b. If 'Termination Criteria' isn't met, then kickstart a new FL round
        # NOTE: We need a way to swap the weights from the initial message
        # in node............
        if not check_termination_criteria():
            print("Going to the next round...")
            results = start_next_round(clients_dict[ClientType.LIBRARY])

    # 8. If 'Termination Criteria' is met...
    # (NOTE: can't and won't happen with step 7.b.)
    if check_termination_criteria():
        # 8.a. Reset all state in the service and mark BUSY as false
        results = stop_session(message.repo_id, clients_dict)

    return results

def handle_no_dataset(message, clients_dict):
    """
    Handle `NO_DATASET` message from a Library. Reduce the number of chosen
    nodes by 1 and then check the continuation/termination criteria again.

    Args:
        message (NoDatasetMessage): The `NO_DATASET` message sent to the server.
        clients_dict (dict): Dictionary of clients, keyed by type of client
            (either `LIBRARY` or `DASHBOARD`).

    Returns:
        dict: Returns a dictionary detailing whether an error occurred and
            if there was no error, what the next action is.
    """
    # 1. Check things match.
    if (state.state["library_type"] == LibraryType.IOS_IMAGE.value \
            or state.state["library_type"] == LibraryType.IOS_TEXT.value) \
            and state.state["dataset_id"] != message.dataset_id:
        error_message = "The dataset ID in the message doesn't match the service's."
        return make_error_results(error_message, ErrorType.NO_DATASET)

    if state.state["session_id"] != message.session_id:
        error_message = "The session ID in the message doesn't match the service's."
        return make_error_results(error_message, ErrorType.NO_DATASET)

    if state.state["current_round"] != message.round:
        error_message = "The round in the message doesn't match the current round."
        return make_error_results(error_message, ErrorType.NO_DATASET)

    # 2. Reduce the number of chosen nodes by 1.
    state.state["num_nodes_chosen"] -= 1

    # 3. If there are no nodes left in this round, cancel the session.
    if state.state["num_nodes_chosen"] == 0:
        state.reset_state(message.repo_id)
        error_message = "No nodes in this round have the specified dataset!"
        client_list = clients_dict[ClientType.DASHBOARD]
        return make_error_results(error_message, ErrorType.NEW_SESSION, \
            action=ActionType.BROADCAST, client_list=client_list)

    # 4. If 'Continuation Criteria' is met...
    if check_continuation_criteria():
        # 4.a. Update round number (+1)
        state.state["current_round"] += 1

        # 4.b. If 'Termination Criteria' isn't met, then kickstart a new FL round
        # NOTE: We need a way to swap the weights from the initial message
        # in node............
        if not check_termination_criteria():
            print("Going to the next round...")
            return start_next_round(clients_dict[ClientType.LIBRARY])

    # 5. If 'Termination Criteria' is met...
    # (NOTE: can't and won't happen with step 7.b.)
    if check_termination_criteria():
        # 4.a. Reset all state in the service and mark BUSY as false
        print("Session finished!")
        return stop_session(message.repo_id, clients_dict)

    return {"action": ActionType.DO_NOTHING, "error": False}


def _do_running_weighted_average(message):
    """
    Runs running weighted average with the new weights and the current weights
    and changes the global state with the result.

    Args:
        message (NewUpdateMessage): The `NEW_UPDATE` message sent to the server.
    """
    key = "current_gradients" if state.state["use_gradients"] else "current_weights"    
    new_values = message.gradients if key == 'current_gradients' else message.weights

    if state.state[key] is None or state.state["sigma_omega"] is None:
        state.state[key] = new_values
        state.state["sigma_omega"] = message.omega
        return

    # Get the variables ready
    current_values = state.state[key]
    sigma_omega = state.state["sigma_omega"]
    new_omega = message.omega

    # Run the math
    temp = np.multiply(current_values, float(sigma_omega))
    temp = np.add(temp, np.multiply(new_values, float(new_omega)))
    new_sigma_omega = sigma_omega + new_omega
    new_weighted_avg = np.divide(temp, float(new_sigma_omega))
    new_weighted_avg = [np.array(avg) for avg in new_weighted_avg]

    # Update state
    state.state[key] = new_weighted_avg
    state.state["sigma_omega"] = new_sigma_omega

def check_continuation_criteria():
    """
    Check the continuation criteria to determine whether we should start the
    next round.

    Right now only implements percentage of nodes averaged.

    TODO: Implement an absolute number of nodes to average (NUM_NODES_AVERAGED).

    Returns:
        bool: Returns `True` if criteria is met, `False` otherwise.
    """
    continuation_criteria = state.state["initial_message"].continuation_criteria

    if "type" not in continuation_criteria:
        raise Exception("Continuation criteria is not well defined.")

    if continuation_criteria["type"] == "PERCENTAGE_AVERAGED":
        if state.state["num_nodes_chosen"] == 0:
            # TODO: Implement a lower bound of how many nodes are needed to
            # continue to the next round.

            # TODO: Count the nodes at the time of averaging instead of at the
            # time of session creation.

            # In the meantime, if 0 nodes were active at the beginning of the
            # session, then the update of the first node to finish training will
            # trigger the continuation criteria.
            return False
        percentage = state.state["num_nodes_averaged"] / state.state["num_nodes_chosen"]
        return continuation_criteria["value"] <= percentage
    else:
        raise Exception("Continuation criteria is not well defined.")


def check_termination_criteria():
    """
    Check the termination criteria to determine whether training is complete.

    Right now only implements a maximum amount of rounds.

    Returns:
        bool: Returns `True` if criteria is met, `False` otherwise.
    """
    termination_criteria = state.state["initial_message"].termination_criteria

    if "type" not in termination_criteria:
        raise Exception("Termination criteria is not well defined.")

    if termination_criteria["type"] == "MAX_ROUND":
        return termination_criteria["value"] < state.state["current_round"]
    else:
        raise Exception("Termination criteria is not well defined.")
