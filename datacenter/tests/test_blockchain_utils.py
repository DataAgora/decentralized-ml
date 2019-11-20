import tests.context
import ipfsapi
import pytest

from core.blockchain.blockchain_utils import getter, setter
from core.configuration import ConfigurationManager


TEST_NONEXISTENT_KEY = 'nonexistence'
TEST_SINGLE_KEY = 'singleton'
TEST_MULTIPLE_KEY = 'multiplicity'
TEST_VALUE = 'World!'

@pytest.fixture(scope='session')
def config():
    config_manager = ConfigurationManager()
    config_manager.bootstrap(
        config_filepath='tests/artifacts/blockchain/configuration.ini'
    )
    return config_manager.get_config()

@pytest.fixture(scope='session')
def ipfs_client(config):
    return ipfsapi.connect(config.get('BLOCKCHAIN', 'host'), 
                            config.getint('BLOCKCHAIN', 'ipfs_port'))

def test_blockchain_utils_getter_nonexistent_key(config, ipfs_client):
    get_val = getter(
        client=ipfs_client,
        key=TEST_NONEXISTENT_KEY,
        local_state=[],
        port=config.getint('BLOCKCHAIN', 'http_port'),
        timeout=config.getint('BLOCKCHAIN', 'timeout')
    )
    assert get_val == [], "Shouldn't have found anything!"

def test_blockchain_utils_setter_simple(config, ipfs_client):
    get_val_before = getter(
        client=ipfs_client,
        key=TEST_SINGLE_KEY,
        local_state=[],
        port=config.getint('BLOCKCHAIN', 'http_port'),
        timeout=config.getint('BLOCKCHAIN', 'timeout')
    )
    tx_receipt = setter(client=ipfs_client,
        key=TEST_SINGLE_KEY,
        port=config.getint('BLOCKCHAIN', 'http_port'),
        round_num=0,
        value=TEST_VALUE,
    )
    assert tx_receipt, "Setting failed"
    get_val_after = getter(
        client=ipfs_client,
        key=TEST_SINGLE_KEY,
        local_state=[],
        port=config.getint('BLOCKCHAIN', 'http_port'),
        timeout=config.getint('BLOCKCHAIN', 'timeout')
    )
    assert get_val_after == get_val_before + [TEST_VALUE], "Setter failed!"

def test_blockchain_utils_setter_multiple_values(config, ipfs_client):
    get_val_before = getter(
        client=ipfs_client,
        key=TEST_MULTIPLE_KEY,
        local_state=[],
        port=config.getint('BLOCKCHAIN', 'http_port'),
        timeout=config.getint('BLOCKCHAIN', 'timeout')
    )
    tx_receipt = setter(client=ipfs_client,
        key=TEST_MULTIPLE_KEY,
        port=config.getint('BLOCKCHAIN', 'http_port'),
        round_num=0,
        value=TEST_VALUE,
    )
    assert tx_receipt, "Setting failed"
    tx_receipt = setter(client=ipfs_client,
        key=TEST_MULTIPLE_KEY,
        port=config.getint('BLOCKCHAIN', 'http_port'),
        round_num=0,
        value=TEST_VALUE,
    )
    assert tx_receipt, "Setting failed"
    get_val_after = getter(
        client=ipfs_client,
        key=TEST_MULTIPLE_KEY,
        local_state=[],
        port=config.getint('BLOCKCHAIN', 'http_port'),
        timeout=config.getint('BLOCKCHAIN', 'timeout')
    )
    assert get_val_after == get_val_before + [TEST_VALUE, TEST_VALUE], \
        "Multi-setter failed!"
