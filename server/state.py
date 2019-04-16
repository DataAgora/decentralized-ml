def init():
    import threading
    global state_lock
    state_lock = threading.Lock()

    global reset_state
    def reset_state():
        global state
        state = {
            "busy": False,
            "session_id": None,
            "current_round": 0,
            "num_nodes_averaged": 0,
            "num_nodes_chosen": 0,
            "current_weights" : None,
            "sigma_omega": None,
            "weights_shape": None,
            "initial_message": None,
            "last_message_time": None,
            "last_message_sent_to_library": None,
            "updatestore_credentials": {
                "table_name": "updatestore_test"
            },
        }

    reset_state()
