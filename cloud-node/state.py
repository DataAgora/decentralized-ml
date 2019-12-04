from model import TEMP_FOLDER
import os
import shutil


def init():
    """Global state for the service."""
    import threading
    global state_lock
    state_lock = threading.Lock()

    global reset_state
    def reset_state():
        global state
        state = {
            "busy": False,
            "session_id": None,
            "repo_id": None,
            "current_round": 0,
            "num_nodes_averaged": 0,
            "num_nodes_chosen": 0,
            "current_weights": None,
            "current_gradients": None,
            "sigma_omega": None,
            "weights_shape": None,
            "initial_message": None,
            "last_message_time": None,
            "last_message_sent_to_library": None,
            "test": False,
            "h5_model_path": None,
        }
        if os.path.isdir(TEMP_FOLDER):
            shutil.rmtree(TEMP_FOLDER)
    reset_state()
