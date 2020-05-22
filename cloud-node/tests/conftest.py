import os
from copy import deepcopy

import pytest
import boto3

import context
import state
from message import Message, ClientType, ActionType, LibraryActionType
from factory import CloudNodeFactory
from protocol import CloudNodeProtocol


@pytest.fixture(autouse=True)
def reset_state(repo_id, api_key):
    state.start_state(repo_id)
    state.state["test"] = True
    yield
    state.reset_state(repo_id)
    state.stop_state()

@pytest.fixture(scope="session")
def library_client():
    return CloudNodeProtocol()

@pytest.fixture(scope="session")
def dashboard_client():
    return CloudNodeProtocol()

@pytest.fixture(scope="session")
def repo_id():
    return "test-repo"

@pytest.fixture(scope="session")
def factory(library_client, dashboard_client, repo_id):
    cloud_factory = CloudNodeFactory()
    cloud_factory.register(library_client, ClientType.LIBRARY, repo_id)
    cloud_factory.register(dashboard_client, ClientType.DASHBOARD, repo_id)
    return cloud_factory

@pytest.fixture(scope="session")
def session_id():
    return "test-session"

@pytest.fixture(scope="session")
def dataset_id():
    return "test-dataset"

@pytest.fixture(scope="session")
def ios_session_id():
    return "ios-test-session"

@pytest.fixture(scope="session")
def api_key():
    return "test-api-key"

@pytest.fixture(scope="session")
def h5_model_path():
    return "cloud-node/tests/artifacts/my_model.h5"

@pytest.fixture(scope="session")
def ios_model_path():
    return "cloud-node/tests/artifacts/ios_model.h5"

@pytest.fixture(scope="session")
def trained_h5_model_path():
    return "cloud-node/tests/artifacts/trained_model.h5"

@pytest.fixture(scope="session")
def model_s3_key(session_id, repo_id):
    return "{0}/{1}/{2}/model.h5".format(repo_id, session_id, 0)

@pytest.fixture(scope="session")
def ios_model_s3_key(ios_session_id, repo_id):
    return "{0}/{1}/{2}/model.h5".format(repo_id, ios_session_id, 0)

@pytest.fixture(scope="session")
def s3_object(model_s3_key):
    s3 = boto3.resource("s3")
    return s3.Object("updatestore", model_s3_key)

@pytest.fixture(scope="session")
def ios_s3_object(ios_model_s3_key):
    s3 = boto3.resource("s3")
    return s3.Object("updatestore", ios_model_s3_key)

@pytest.fixture(scope="session")
def hyperparams():
    return {
        "batch_size": 100,
        "epochs": 5,
        "shuffle": True,
    }

@pytest.fixture(scope="session")
def session_message(repo_id, session_id, hyperparams):
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
        "ios_config": {},
    }

@pytest.fixture(scope="session")
def ios_config():
    ios_config = {
        "data_type": "image",
        "image_config": {
            "dims": (28, 28),
            "color_space": "GRAYSCALE",
        },
        "class_labels": [str(i) for i in range(10)]
    }
    return ios_config

@pytest.fixture(scope="session")
def python_session_message(session_message):
    python_message = deepcopy(session_message)
    python_message["library_type"] = "PYTHON"
    return Message.make(python_message)

@pytest.fixture(scope="session")
def js_session_message(session_message):
    js_message = deepcopy(session_message)
    js_message["library_type"] = "JAVASCRIPT"
    return Message.make(js_message)

@pytest.fixture(scope="session")
def ios_session_message(session_message, ios_session_id, ios_config, \
        dataset_id):
    ios_message = deepcopy(session_message)
    ios_message["session_id"] = ios_session_id
    ios_message["library_type"] = "IOS"
    ios_message["ios_config"] = ios_config
    ios_message["dataset_id"] = dataset_id
    return Message.make(ios_message)

@pytest.fixture(scope="session")
def train_message(session_id, repo_id, hyperparams):
    return {
        "error": False,
        "session_id": session_id,
        "repo_id": repo_id,
        "round": 1,
        "action": LibraryActionType.TRAIN.value,
        "hyperparams": hyperparams,
    }

@pytest.fixture(scope="session")
def ios_train_message(train_message, ios_session_id, dataset_id):
    ios_train_message = deepcopy(train_message)
    ios_train_message["session_id"] = ios_session_id
    ios_train_message["dataset_id"] = dataset_id
    return ios_train_message

@pytest.fixture(scope="session")
def no_action_message(ios_session_id, dataset_id):
    return {
        "action": ActionType.DO_NOTHING,
        "error": False,
    }
    