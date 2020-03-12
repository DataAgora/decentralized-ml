import os
from copy import deepcopy

import pytest
from keras.models import load_model

import state
from message import Message
from new_message import process_new_message


@pytest.fixture(autouse=True)
def reset_state():
    state.reset_state()

@pytest.fixture(autouse=True)
def simple_training_state(ios_session_id, repo_id, ios_session_message, \
        dataset_id):
    return {
        "busy": True,
        "session_id": ios_session_id,
        "repo_id": repo_id,
        "dataset_id": dataset_id,
        "current_round": 1,
        "num_nodes_chosen": 2,
        "num_nodes_averaged": 0,
        "initial_message": ios_session_message,
        "last_message_time": None,
        "last_message_sent_to_library": None,
        "use_gradients": True,
        "current_gradients": None,
        "library_type": "IOS_IMAGE",
        "checkpoint_frequency": 1,
        "test": True
    }

@pytest.fixture(autouse=True)
def complex_training_state(ios_model_path, ios_session_id, \
        simple_training_state, ios_config, hyperparams, dataset_id):
    session_h5_model_folder = os.path.join("temp", ios_session_id)
    session_h5_model_path = os.path.join(session_h5_model_folder, "model.h5")

    if not os.path.isdir(session_h5_model_folder):
        os.makedirs(session_h5_model_folder)
    old_model = load_model(ios_model_path)
    old_model.save(session_h5_model_path)

    complex_state = deepcopy(simple_training_state)
    complex_state["num_nodes_averaged"] = 1
    complex_state["h5_model_path"] = ios_model_path
    complex_state["ios_config"] = ios_config
    complex_state["hyperparams"] = hyperparams
    complex_state["dataset_id"] = dataset_id

    return complex_state

@pytest.fixture(scope="session")
def no_dataset_message(ios_session_id, dataset_id):
    return Message.make({
        "session_id": ios_session_id,
        "dataset_id": dataset_id,
        "round": 1,
        "type": "NO_DATASET",
    })

@pytest.fixture
def ios_broadcast_message(ios_train_message, factory, ios_session_id):
    ios_train_message["round"] = 2
    return {
        "error": False,
        "action": "BROADCAST",
        "client_list": factory.clients["LIBRARY"],
        "message": ios_train_message,
    }

def test_simple_no_dataset_message(simple_training_state, no_dataset_message, \
        factory, library_client, no_action_message):
    """
    Test that a client sending a `NO_DATASET` message reduces the number of
    chosen nodes and results in no further action taken when the continuation
    criteria is not fulfilled.
    """
    state.state = simple_training_state
    results = process_new_message(no_dataset_message, factory, \
        library_client)

    assert state.state["num_nodes_chosen"] == 1
    assert results == no_action_message, "Resulting message is incorrect!"

def test_complex_no_dataset_message(complex_training_state, no_dataset_message, \
        factory, library_client, ios_broadcast_message):
    """
    Test that a client sending a `NO_DATASET` message reduces the number of
    chosen nodes and results in the next round when the continuation
    criteria is fulfilled.
    """
    state.state = complex_training_state
    results = process_new_message(no_dataset_message, factory, \
        library_client)

    assert state.state["num_nodes_chosen"] == 1
    assert results == ios_broadcast_message, "Resulting message is incorrect!"
