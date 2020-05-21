import json
import os

import pytest
from keras.models import load_model
import numpy as np

import state
from message import Message, MessageType, ClientType, ActionType, \
    LibraryActionType, ErrorType
from new_message import process_new_message


@pytest.fixture(autouse=True)
def set_training_state(repo_id, session_id, python_session_message, \
        h5_model_path):
    session_h5_model_folder = os.path.join("temp", repo_id, session_id)
    session_h5_model_path = os.path.join(session_h5_model_folder, "model.h5")

    if not os.path.isdir(session_h5_model_folder):
        os.makedirs(session_h5_model_folder)
    old_model = load_model(h5_model_path)
    old_model.save(session_h5_model_path)

    state.state = {
        "busy": True,
        "session_id": session_id,
        "repo_id": repo_id,
        "current_round": 1,
        "num_nodes_chosen": 1,
        "num_nodes_averaged": 0,
        "initial_message": python_session_message,
        "last_message_time": None,
        "last_message_sent_to_library": None,
        "h5_model_path": session_h5_model_path,
        "use_gradients": True,
        "current_gradients": None,
        "library_type": "PYTHON",
        "checkpoint_frequency": 1,
        "test": True
    }
    

@pytest.fixture(scope="module")
def simple_gradients(h5_model_path, trained_h5_model_path):
    old_model = load_model(h5_model_path)
    old_model_weights = old_model.get_weights()

    trained_model = load_model(trained_h5_model_path)
    trained_model_weights = trained_model.get_weights()

    return np.subtract(old_model_weights, trained_model_weights)

@pytest.fixture(scope="module")
def simple_new_update_message(repo_id, session_id, simple_gradients):
    simple_gradients = [gradient.tolist() for gradient in simple_gradients]
    return Message.make({
        "repo_id": repo_id,
        "session_id": session_id,
        "action": LibraryActionType.TRAIN.value,
        "results": {
            "gradients": simple_gradients,
            "omega": 8000,
        },
        "round": 1,
        "type": MessageType.NEW_UPDATE.value,
    })  

@pytest.fixture
def broadcast_message(simple_gradients, factory, repo_id, train_message):
    train_message["round"] = 2
    return {
        "action": ActionType.BROADCAST,
        "client_list": factory.clients[repo_id][ClientType.LIBRARY],
        "message": train_message,
    }

def test_simple_aggregation(simple_new_update_message, factory, \
        library_client, simple_gradients, broadcast_message):
    """
    Test that aggregation after one round succeeds and continues to the next
    round.
    """
    results = process_new_message(simple_new_update_message, factory, \
        library_client)
    
    message_gradients = results["message"].pop("gradients")
    simple_gradients = [gradient.tolist() for gradient in simple_gradients]
    
    assert broadcast_message == results, "Resulting message is incorrect!"
    
    for simple_gradient, message_gradient in zip(simple_gradients, message_gradients):
        assert np.allclose(message_gradient, simple_gradient), \
            "Gradients not equal!"   
