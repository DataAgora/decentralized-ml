from copy import deepcopy

import pytest
import boto3

import context
from message import Message
from factory import CloudNodeFactory
from protocol import CloudNodeProtocol


@pytest.fixture(scope="session")
def library_client():
    return CloudNodeProtocol()

@pytest.fixture(scope="session")
def dashboard_client():
    return CloudNodeProtocol()

@pytest.fixture(scope="session")
def factory(library_client, dashboard_client):
    cloud_factory = CloudNodeFactory()
    cloud_factory.register(library_client, "LIBRARY")
    cloud_factory.register(dashboard_client, "DASHBOARD")
    return cloud_factory

@pytest.fixture(scope="session")
def session_id():
    return "test-session"

@pytest.fixture(scope="session")
def ios_session_id():
    return "ios-test-session"

@pytest.fixture(scope="session")
def repo_id():
    return "test-repo"

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
        "ios_config": {}
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
def ios_session_message(session_message, ios_session_id, ios_config):
    ios_message = deepcopy(session_message)
    ios_message["session_id"] = ios_session_id
    ios_message["library_type"] = "IOS"
    ios_message["ios_config"] = ios_config
    return Message.make(ios_message)

@pytest.fixture(scope="session")
def train_message(session_id, repo_id, hyperparams):
    return {
        "session_id": session_id,
        "repo_id": repo_id,
        "round": 1,
        "action": "TRAIN",
        "hyperparams": hyperparams,
    }
