import os
from copy import deepcopy

import pytest

import state
from message import ClientType, ActionType
from new_message import process_new_message


@pytest.fixture
def broadcast_message(factory, repo_id, train_message):
    return {
        "action": ActionType.BROADCAST,
        "client_list": factory.clients[repo_id][ClientType.LIBRARY],
        "message": train_message,
    }

@pytest.fixture
def ios_broadcast_message(ios_train_message, factory, repo_id):
    return {
        "action": ActionType.BROADCAST,
        "client_list": factory.clients[repo_id][ClientType.LIBRARY],
        "message": ios_train_message,
    }

@pytest.fixture(autouse=True, scope="module")
def manage_test_object(repo_id, s3_object, ios_s3_object, h5_model_path, \
        ios_model_path):
    s3_object.put(Body=open(h5_model_path, "rb"))
    ios_s3_object.put(Body=open(ios_model_path, "rb"))
    yield
    s3_object.delete()
    ios_s3_object.delete()
    state.reset_state(repo_id)    

def test_session_while_busy(python_session_message, factory, \
        dashboard_client):
    """
    Test that new session cannot be started while server is busy.
    """
    state.state["busy"] = True
    state.num_sessions = 1

    results = process_new_message(python_session_message, factory, 
        dashboard_client)
    message = results["message"]

    assert message["error"], "Error should have occurred!"
    assert message["error_message"] == "Server is already busy working."
    assert state.num_sessions == 1, "Number of sessions should be 1!"

def test_new_python_session(python_session_message, factory, \
        broadcast_message, dashboard_client):
    """
    Test that new session with Python library produces correct `BROADCAST`
    message and that model is successfully saved.
    """
    results = process_new_message(python_session_message, factory, \
        dashboard_client)

    assert state.state["h5_model_path"], "h5 model path not set!"
    assert os.path.isfile(state.state["h5_model_path"]), "Model not saved!"

    assert results == broadcast_message, "Resulting message is incorrect!"
    assert state.num_sessions == 1, "Number of sessions should be 1!"
    

def test_new_js_session(js_session_message, factory, broadcast_message, \
        dashboard_client):
    """
    Test that new session with Javascript library produces correct `BROADCAST`
    message and that model is successfully saved and converted.
    """
    results = process_new_message(js_session_message, factory, \
        dashboard_client)

    assert state.state["h5_model_path"], "h5 model path not set!"
    assert os.path.isfile(state.state["h5_model_path"]), "Model not saved!"
    
    assert state.state["tfjs_model_path"], "TFJS model path not set."
    assert os.path.isdir(state.state["tfjs_model_path"]) \
        and len(os.listdir(state.state["tfjs_model_path"])) > 0, \
        "TFJS model conversion failed!"

    assert results == broadcast_message, "Resulting message is incorrect!"
    assert state.num_sessions == 1, "Number of sessions should be 1!"

def test_new_ios_session(ios_session_message, factory, ios_broadcast_message, \
        dashboard_client):
    """
    Test that new session with Javascript library produces correct `BROADCAST`
    message and that model is successfully saved and converted.
    """
    results = process_new_message(ios_session_message, factory, \
        dashboard_client)

    assert state.state["h5_model_path"], "h5 model path not set!"
    assert os.path.isfile(state.state["h5_model_path"]), "Model not saved!"
    
    assert state.state["mlmodel_path"], "MLModel path not set."
    assert os.path.isfile(state.state["mlmodel_path"]), \
        "iOS model conversion failed!"

    assert results == ios_broadcast_message, "Resulting message is incorrect!"
    assert state.num_sessions == 1, "Number of sessions should be 1!"
    