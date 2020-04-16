import json
import os

import pytest

import state
from protocol import CloudNodeProtocol
from new_message import process_new_message
from message import Message


@pytest.fixture(autouse=True)
def reset_state(api_key):
    os.environ["API_KEY"] = api_key
    state.reset_state()

@pytest.fixture(scope="module")
def dummy_client():
    return CloudNodeProtocol()

@pytest.fixture(scope="module")
def library_registration_message(api_key):
    return Message.make({
        "type": "REGISTER",
        "node_type": "library",
        "api_key": api_key,
    })

@pytest.fixture(scope="module")
def bad_registration_message():
    return Message.make({
        "type": "REGISTER",
        "node_type": "library",
        "api_key": "bad-api-key",
    })

@pytest.fixture(scope="module")
def dashboard_registration_message(api_key):
    return Message.make({
        "type": "REGISTER",
        "node_type": "dashboard",
        "api_key": api_key,
    })

@pytest.fixture(scope="module")
def do_nothing():
    return {
        "action": None
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
def original_client_count(factory):
    return _client_count(factory)

@pytest.fixture(autouse=True)
def unregister(factory, dummy_client):
    yield
    factory.unregister(dummy_client)

def test_basic_register(library_registration_message, factory, dummy_client, \
        do_nothing, original_client_count):
    """
    Test that a basic `LIBRARY` registration succeeds.
    """
    results = process_new_message(library_registration_message, factory, \
        dummy_client)
    new_client_count = _client_count(factory)
    
    assert results == do_nothing, "Resulting message is incorrect!"
    assert new_client_count == original_client_count + 1, \
        "Client count is incorrect!"

def test_failed_authentication(bad_registration_message, factory, \
        dummy_client, failed_authentication_error, original_client_count):
    """
    Test that registration fails with an invalid API key
    """
    bad_registration_message.api_key = "bad-api-key"
    results = process_new_message(bad_registration_message, factory, \
        dummy_client)
    new_client_count = _client_count(factory)

    assert results.get("message") == failed_authentication_error, \
        "Resulting message is incorrect!"
    assert new_client_count == original_client_count, \
        "Client count is incorrect!"

def test_no_duplicate_client(library_registration_message, factory, \
        dummy_client, duplicate_client_error, original_client_count):
    """
    Test that a client cannot be registered twice.
    """
    results = process_new_message(library_registration_message, factory, \
        dummy_client)
    results = process_new_message(library_registration_message, factory, \
        dummy_client)
    new_client_count = _client_count(factory)
    
    assert results.get("message") == duplicate_client_error, \
        "Resulting message is incorrect!"
    assert new_client_count == original_client_count + 1, \
        "Client count is incorrect!"

def test_only_one_dashboard_client(dashboard_registration_message, factory, \
        dummy_client, only_one_dashboard_client_error, original_client_count):
    """
    Test that more than one dashboard client cannot be registered at a time.
    """
    assert _client_count(factory) == original_client_count
    results = process_new_message(dashboard_registration_message, factory, \
        dummy_client)
    new_client_count = _client_count(factory)

    assert results.get("message") == only_one_dashboard_client_error, \
        "Resulting message is incorrect!"
    assert new_client_count == original_client_count, \
        "Client count is incorrect!"

def _client_count(factory):
    """
    Helper function to count the total number of clients in the factory.
    """
    return len(factory.clients["DASHBOARD"]) + len(factory.clients["LIBRARY"])
