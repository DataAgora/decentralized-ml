import time
import logging

import numpy as np

import state
from updatestore import store_update
from coordinator import start_next_round, stop_session
from model import swap_weights


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
    results = {"action": None, "error": False}

    # 1. Check things match.
    if state.state["session_id"] != message.session_id:
        return {
            "error": True,
            "message": "The session id in the message doesn't match the service's."
        }

    if state.state["current_round"] != message.round:
        return {
            "error": True,
            "message": "The round in the message doesn't match the current round."
        }

    # 2 Lock section/variables that will be changed...
    state.state_lock.acquire()

    state.state["last_message_time"] = time.time()

    # 3. Do running weighted average on the new weights.
    _do_running_weighted_average(message)

    # 4. Update the number of nodes averaged (+1)
    state.state["num_nodes_averaged"] += 1

    # 5. Log this update.
    # NOTE: Disabled until we actually need it. Could be useful for a progress bar.
    # store_update("UPDATE_RECEIVED", message, with_weights=False)
    
    # 6. Swap in the newly averaged weights for this model.
    swap_weights()

    # 7. Store the model in S3, following checkpoint frequency constraints.
    if state.state["current_round"] % state.state["checkpoint_frequency"] == 0:
        store_update("ROUND_COMPLETED", message)

    # 8. If 'Continuation Criteria' is met...
    if check_continuation_criteria():
        # 8.a. Update round number (+1)
        state.state["current_round"] += 1

        # 8.b. If 'Termination Criteria' isn't met, then kickstart a new FL round
        # NOTE: We need a way to swap the weights from the initial message
        # in node............
        if not check_termination_criteria():
            print("Going to the next round...")
            results = start_next_round(clients_dict["LIBRARY"])

    # 9. If 'Termination Criteria' is met...
    # (NOTE: can't and won't happen with step 8.b.)
    if check_termination_criteria():
        # 9.a. Reset all state in the service and mark BUSY as false
        return stop_session(clients_dict)

    # 10. Release section/variables that were changed...
    state.state_lock.release()

    return results

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
            return True
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
