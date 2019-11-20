import time
import logging

import numpy as np

import state
from updatestore import store_update
from coordinator import start_next_round


logging.basicConfig(level=logging.DEBUG)

def handle_new_weights(message, clients_dict):
    """
    Handle new weights from a Library.
    """
    results = {"error": False, "message": "Success."}

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
    do_running_weighted_average(message)

    # 4. Update the number of nodes averaged (+1)
    state.state["num_nodes_averaged"] += 1

    # 5. Log this update.
    # NOTE: Disabled until we actually need it. Could be useful for a progress bar.
    # store_update("UPDATE_RECEIVED", message, with_weights=False)

    # 6. If 'Continuation Criteria' is met...
    if check_continuation_criteria(state.state["initial_message"].continuation_criteria):
        # 6.a. Update round number (+1)
        state.state["current_round"] += 1

        # 6.b. If 'Termination Criteria' isn't met, then kickstart a new FL round
        # NOTE: We need a way to swap the weights from the initial message
        # in node............
        if not check_termination_criteria(state.state["initial_message"].termination_criteria):
            print("Going to the next round...")
            results = kickstart_new_round(clients_dict["LIBRARY"])

            # 6.c. Log the resulting weights for the user (for this round)
            store_update("ROUND_COMPLETED", message)

    # 7. If 'Termination Criteria' is met...
    # (NOTE: can't and won't happen with step 6.c.)
    if check_termination_criteria(state.state["initial_message"].termination_criteria):
        # 7.a. Reset all state in the service and mark BUSY as false
        state.reset_state()

    # 8. Release section/variables that were changed...
    state.state_lock.release()

    return results


def kickstart_new_round(clients_list):
    """
    Selects new nodes to run federated averaging with, and passes them the new
    averaged model.
    """
    # Make the new message with new round (weights are swapped in the coordinator)
    new_message = state.state["initial_message"]
    new_message.round = state.state["current_round"]

    # Start a new round
    return start_next_round(new_message, clients_list)


def do_running_weighted_average(message):
    """
    Runs running weighted average with the new weights and the current weights
    and changes the global state with the result.
    """
    # If this is the first weights we're averaging, just update them and return
    if state.state["current_weights"] is None or state.state["sigma_omega"] is None:
        state.state["current_weights"] = message.weights
        state.state["sigma_omega"] = message.omega
        return

    # Get the variables ready
    current_weights = state.state["current_weights"]
    sigma_omega = state.state["sigma_omega"]
    new_weights = message.weights
    new_omega = message.omega

    # Run the math
    temp = np.multiply(current_weights, float(sigma_omega))
    temp = np.add(temp, np.multiply(new_weights, float(new_omega)))
    new_sigma_omega = sigma_omega + new_omega
    new_weighted_avg = np.divide(temp, float(new_sigma_omega))

    # Update state
    state.state["current_weights"] = new_weighted_avg
    state.state["sigma_omega"] = new_sigma_omega


def check_continuation_criteria(continuation_criteria):
    """
    Right now only implements percentage of nodes averaged.

    TODO: Implement an absolute number of nodes to average (NUM_NODES_AVERAGED).
    """
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


def check_termination_criteria(termination_criteria):
    """
    Right now only implements a maximum amount of rounds.
    """
    if "type" not in termination_criteria:
        raise Exception("Termination criteria is not well defined.")

    if termination_criteria["type"] == "MAX_ROUND":
        return termination_criteria["value"] < state.state["current_round"]
    else:
        raise Exception("Termination criteria is not well defined.")
