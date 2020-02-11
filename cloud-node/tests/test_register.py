import json

import pytest

from protocol import CloudNodeProtocol
from new_message import process_new_message
from message import Message


@pytest.fixture(scope="module")
def dummy_client():
    return CloudNodeProtocol()

@pytest.fixture(scope="module")
def library_registration_message():
    return Message.make({
        "type": "REGISTER",
        "node_type": "library"
    })

@pytest.fixture(scope="module")
def dashboard_registration_message():
    return Message.make({
        "type": "REGISTER",
        "node_type": "dashboard"
    })

@pytest.fixture(scope="module")
def do_nothing():
    return {
        "error": False,
        "action": None
    }

@pytest.fixture(scope="module")
def duplicate_client_error():
    return {
        "error": True,
        "message": "Client already exists!"
    }

@pytest.fixture(scope="module")
def only_one_dashboard_client_error():
    return {
        "error": True,
        "message": "Only one DASHBOARD client allowed at a time!"
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

def test_no_duplicate_client(library_registration_message, factory, \
        dummy_client, duplicate_client_error, original_client_count):
    """
    Test that a client cannot be registered twice.
    """
    results = process_new_message(library_registration_message, factory, \
        dummy_client)
    results = process_new_message(library_registration_message, factory, \
        dummy_client)
    print(results)
    new_client_count = _client_count(factory)
    
    assert results == duplicate_client_error, \
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

    assert results == only_one_dashboard_client_error, \
        "Resulting message is incorrect!"
    assert new_client_count == original_client_count, \
        "Client count is incorrect!"


def _client_count(factory):
    """
    Helper function to count the total number of clients in the factory.
    """
    return len(factory.clients["DASHBOARD"]) + len(factory.clients["LIBRARY"])
