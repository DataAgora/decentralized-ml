import os

import pytest

import state
from new_message import process_new_message


@pytest.fixture
def broadcast_message(factory, train_message):
    return {
        "error": False,
        "action": "BROADCAST",
        "client_list": factory.clients["LIBRARY"],
        "message": train_message,
    }
    
@pytest.fixture(autouse=True)
def reset_state():
    state.reset_state()

@pytest.fixture(autouse=True, scope="module")
def manage_test_object(s3_object, h5_model_path):
    s3_object.put(Body=open(h5_model_path, "rb"))
    yield
    s3_object.delete()
    state.reset_state()    

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

def test_session_while_busy(python_session_message, factory, \
        dashboard_client):
    """
    Test that new session cannot be started while server is busy.
    """
    state.state["busy"] = True

    results = process_new_message(python_session_message, factory, 
        dashboard_client)

    assert results["error"], "Error should have occurred!"
    assert results["message"] == "Server is already busy working."

    