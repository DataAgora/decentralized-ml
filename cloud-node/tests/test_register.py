import json
import os

import pytest

import state
from protocol import CloudNodeProtocol
from new_message import process_new_message
from message import Message


@pytest.fixture(scope="module")
def dummy_client():
    return CloudNodeProtocol()

@pytest.fixture(scope="module")
def library_registration_message(repo_id, api_key):
    return Message.make({
        "type": "REGISTER",
        "node_type": "library",
        "repo_id": repo_id,
        "api_key": api_key,
    })

@pytest.fixture(scope="module")
def bad_registration_message(repo_id):
    return Message.make({
        "type": "REGISTER",
        "node_type": "library",
        "repo_id": repo_id,
        "api_key": "bad-api-key",
    })

@pytest.fixture(scope="module")
def dashboard_registration_message(repo_id, api_key):
    return Message.make({
        "type": "REGISTER",
        "node_type": "dashboard",
        "repo_id": repo_id,
        "api_key": api_key,
    })

@pytest.fixture(scope="module")
def do_nothing():
    return {
        "action": None
    }

@pytest.fixture(scope="module")
def registration_success():
    return {
        "action": "UNICAST",
        "message": {
            "action": "REGISTRATION_SUCCESS",
            "error": False,
        }
    }

@pytest.fixture(scope="module")
def failed_authentication_error():
    return {
        "error": True,
        "error_message": "API key provided is invalid!",
        "type": "AUTHENTICATION",
    }

@pytest.fixture(scope="module")
def duplicate_client_error():
    return {
        "error": True,
        "error_message": "Client already exists!",
        "type": "REGISTRATION",
    }

@pytest.fixture(scope="module")
def only_one_dashboard_client_error():
    return {
        "error": True,
        "error_message": "Only one DASHBOARD client allowed at a time!",
        "type": "REGISTRATION",
    }

@pytest.fixture(scope="module")
def original_client_count(factory, repo_id):
    return _client_count(factory, repo_id)

@pytest.fixture(autouse=True)
def unregister(factory, dummy_client):
    yield
    factory.unregister(dummy_client)

def test_basic_register(library_registration_message, factory, dummy_client, \
        registration_success, original_client_count):
    """
    Test that a basic `LIBRARY` registration succeeds.
    """
    repo_id = library_registration_message.repo_id
    results = process_new_message(library_registration_message, factory, \
        dummy_client)
    new_client_count = _client_count(factory, repo_id)
    
    assert results == registration_success, \
        "Resulting message is incorrect!"
    assert new_client_count == original_client_count + 1, \
        "Client count is incorrect!"

def test_failed_authentication(bad_registration_message, factory, \
        dummy_client, failed_authentication_error, original_client_count):
    """
    Test that registration fails with an invalid API key
    """
    repo_id = bad_registration_message.repo_id
    bad_registration_message.api_key = "bad-api-key"
    results = process_new_message(bad_registration_message, factory, \
        dummy_client)
    new_client_count = _client_count(factory, repo_id)

    assert results.get("message") == failed_authentication_error, \
        "Resulting message is incorrect!"
    assert new_client_count == original_client_count, \
        "Client count is incorrect!"

def test_no_duplicate_client(library_registration_message, factory, \
        dummy_client, duplicate_client_error, original_client_count):
    """
    Test that a client cannot be registered twice.
    """
    repo_id = library_registration_message.repo_id
    results = process_new_message(library_registration_message, factory, \
        dummy_client)
    results = process_new_message(library_registration_message, factory, \
        dummy_client)
    new_client_count = _client_count(factory, repo_id)
    
    assert results.get("message") == duplicate_client_error, \
        "Resulting message is incorrect!"
    assert new_client_count == original_client_count + 1, \
        "Client count is incorrect!"

def test_only_one_dashboard_client(dashboard_registration_message, factory, \
        dummy_client, only_one_dashboard_client_error, original_client_count):
    """
    Test that more than one dashboard client cannot be registered at a time.
    """
    repo_id = dashboard_registration_message.repo_id
    assert _client_count(factory, repo_id) == original_client_count
    results = process_new_message(dashboard_registration_message, factory, \
        dummy_client)
    new_client_count = _client_count(factory, repo_id)

    assert results.get("message") == only_one_dashboard_client_error, \
        "Resulting message is incorrect!"
    assert new_client_count == original_client_count, \
        "Client count is incorrect!"

def _client_count(factory, repo_id):
    """
    Helper function to count the total number of clients in the factory.
    """
    return len(factory.clients[repo_id]["DASHBOARD"]) + len(factory.clients[repo_id]["LIBRARY"])
