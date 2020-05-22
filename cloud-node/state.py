from model import TEMP_FOLDER
import os
import shutil


def init():
    """Global state for the service."""
    import threading
    state_lock = threading.Lock()
    states = {}

    global state
    state = None

    global num_sessions
    num_sessions = 0

    global reset_state
    def reset_state(repo_id):
        global state
        if state and state["busy"]:
            global num_sessions
            num_sessions -= 1

        states[repo_id] = {
            "busy": False,
            "session_id": None,
            "dataset_id": None,
            "repo_id": repo_id,
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
            "library_type": None,
            "ios_type": None
        }
        
        temp_folder = os.path.join(TEMP_FOLDER, repo_id)
        if os.path.isdir(temp_folder):
            shutil.rmtree(temp_folder)

    global start_state
    def start_state(repo_id):
        state_lock.acquire()
        if repo_id not in states:
            reset_state(repo_id)
        global state
        state = states[repo_id]

    global stop_state
    def stop_state():
        global state
        state = None
        state_lock.release()

    global start_state_by_session_id
    def start_state_by_session_id(session_id):
        for repo_id, state in states.items():
            if state["session_id"] == session_id:
                start_state(repo_id)
                return repo_id
        return None
