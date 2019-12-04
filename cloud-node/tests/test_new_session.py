import context

import os
import json
from copy import deepcopy

import pytest
import boto3

import state
from coordinator import start_new_session
from message import Message

@pytest.fixture(scope="session")
def session_id():
    return "test-session"

@pytest.fixture(scope="session")
def repo_id():
    return "test-repo"

@pytest.fixture(scope="session")
def h5_model_path():
    return "cloud-node/tests/artifacts/my_model.h5"

@pytest.fixture(scope="session")
def model_s3_key(session_id, repo_id):
    return "{0}/{1}/{2}/model.h5".format(repo_id, session_id, 0)

@pytest.fixture(scope="session")
def s3_object(model_s3_key):
    s3 = boto3.resource("s3")
    return s3.Object("updatestore", model_s3_key)

@pytest.fixture
def hyperparams():
    return {
        "batch_size": 100,
        "epochs": 5,
        "shuffle": True,
    }

@pytest.fixture
def dummy_clients():
    return ["clients"]

@pytest.fixture
def sample_good_session_message(repo_id, session_id, hyperparams, \
        model_s3_key):
    return {
        "type": "NEW_SESSION",
        "repo_id": repo_id,
        "session_id": session_id,
        "hyperparams": hyperparams,
        "checkpoint_frequency": 1,
        "selection_criteria": {
            "type": "ALL_NODES",
        },
        "continuation_criteria": {
            "type": "PERCENTAGE_AVERAGED",
            "value": 0.75
        },
        "termination_criteria": {
            "type": "MAX_ROUND",
            "value": 5
        },
        "model_s3_key": model_s3_key
    }

@pytest.fixture
def good_python_session_message(sample_good_session_message):
    python_message = deepcopy(sample_good_session_message)
    python_message["library_type"] = "PYTHON"
    return Message.make(python_message)

@pytest.fixture
def good_js_session_message(sample_good_session_message):
    js_message = deepcopy(sample_good_session_message)
    js_message["library_type"] = "JAVASCRIPT"
    return json.dumps(js_message)

@pytest.fixture
def train_message(session_id, repo_id, hyperparams):
    return {
        "session_id": session_id,
        "repo_id": repo_id,
        "round": 1,
        "action": "TRAIN",
        "hyperparams": hyperparams,
    }

@pytest.fixture
def broadcast_message(dummy_clients, train_message):
    return {
        "error": False,
        "action": "BROADCAST",
        "client_list": dummy_clients,
        "message": train_message,
    }
@pytest.fixture(autouse=True, scope="session")
def manage_test_object(s3_object, h5_model_path):
    s3_object.put(Body=open(h5_model_path, "rb"))
    yield
    s3_object.delete()
    state.reset_state()    

def test_new_python_session(good_python_session_message, dummy_clients, \
        broadcast_message):
    results = start_new_session(good_python_session_message, dummy_clients)

    assert state.state["h5_model_path"], "h5 model path not set!"
    assert os.path.isfile(state.state["h5_model_path"]), "Model not saved!"
    assert results == broadcast_message, "Broadcast message is incorrect!"

    