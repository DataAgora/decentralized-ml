import uuid

from state import state
from model import decode_weights, keras_2_tfjs
from message import Message

def start_new_session(serialized_message, clients_list):

    # // 1. If server is BUSY, error. Otherwise, mark the service as BUSY.
    if state.state["busy"]:
        return {
            "error": True,
            "message": "Server is already busy working."
        }
    state.state["busy"] = True

    # // 2. Decode new message from Explora with:
    # //    - Metadata (user, repo, logging info)
    # //    - Model + weights + optimizer (in .h5 binary format)
    # //    - Hyperparameters (batch size, learning rate, decay)
    # //    - Selection Criteria (i.e., nodes with more than 1000 data points)
    # //    - Continuation Criteria (i.e., 80% of selected nodes weights averaged)
    # //    - Termination Criteria (i.e., 20 FL rounds completed)
    message = Message(serialized_message)

    # // 3. Set the internal round variable to 1, reset the number of nodes
    # //    averaged to 0, update the initial message.
    state.state["current_round"] = 1
    state.state["num_nodes_averaged"] = 0
    state.state["initial_message"] = serialized_message
    state.state["session_id"] = str(uuid.uuid4())

    # // 4. According to the 'Selection Criteria', choose clients to forward
    # //    training messages to.
    chosen_clients = _choose_clients(message.selection_criteria, clients_list)
    state.state["num_nodes_chosen"] = len(chosen_clients)

    # // 5. Convert .h5 model into TFJS model
    # // NOTE/TODO: This may have to be 'served' to the client and not passed...
    tfjs_model = keras_2_tfjs(message.h5_model)

    # // 6. Kickstart a DML Session with the TFJS model and round # 1
    return {
        "error": False,
        "action": "broadcast",
        "client_list": chosen_clients,
        "message": {
            "session_id": state.state["session_id"],
            "round": 1,
            "model": tfjs_model,
            # message to client nodes TBD
        }
    }


def _choose_clients(selection_criteria, client_list):
    """
    TO BE IMPLEMENTED.

    Need to define a selection criteria object first.

    Right now it just chooses all clients.
    """
    return client_list
