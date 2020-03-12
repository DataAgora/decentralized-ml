import os
import json

import pytest
import numpy as np

import state
from parse_weights import calculate_new_weights, read_compiled_weights


@pytest.fixture(autouse=True)
def reset_state():
    state.reset_state()

@pytest.fixture(scope="session")
def simple_gradients_path():
    return "cloud-node/tests/artifacts/simple_gradients.json"

@pytest.fixture(scope="session")
def complex_gradients_path():
    return "cloud-node/tests/artifacts/complex_gradients.json"

@pytest.fixture(scope="session")
def new_weights_path():
    return "cloud-node/tests/artifacts/new_weights"

@pytest.fixture(scope="session")
def old_simple_weights_path():
    return "cloud-node/tests/artifacts/old_simple_weights"

@pytest.fixture(scope="session")
def new_simple_weights_path():
    return "cloud-node/tests/artifacts/new_simple_weights"

@pytest.fixture(scope="session")
def old_complex_weights_path():
    return "cloud-node/tests/artifacts/old_complex_weights"

@pytest.fixture(scope="session")
def new_complex_weights_path():
    return "cloud-node/tests/artifacts/new_complex_weights"

@pytest.fixture(scope="session")
def simple_gradients(simple_gradients_path):
    with open(simple_gradients_path, 'r') as f:
        gradients = [np.array(grad) for grad in json.load(f)]
        return np.array(gradients)

@pytest.fixture(scope="session")
def complex_gradients(complex_gradients_path):
    with open(complex_gradients_path, 'r') as f:
        gradients = [np.array(grad) for grad in json.load(f)]
        return np.array(gradients)

@pytest.fixture(autouse=True)
def remove_weights(new_weights_path):
    yield
    if os.path.isfile(new_weights_path):
        os.remove(new_weights_path)

def test_parse_simple_weights(simple_gradients, old_simple_weights_path, \
        new_simple_weights_path, new_weights_path):
    state.state["current_gradients"] = simple_gradients
    new_weights = calculate_new_weights(old_simple_weights_path, \
        new_weights_path, lr=0.01)
    
    new_expected_weights = read_compiled_weights(new_simple_weights_path)
    new_actual_weights = read_compiled_weights(new_weights_path)

    for new_weight, new_expected_weight, new_actual_weight \
            in zip(new_weights, new_expected_weights, new_actual_weights):
        assert np.allclose(new_weight, new_expected_weight), \
            "Weights not read correctly!"
        assert np.allclose(new_actual_weight, new_expected_weight), \
            "Weights not written correctly!"

def test_parse_complex_weights(complex_gradients, old_complex_weights_path, \
        new_complex_weights_path, new_weights_path):
    state.state["current_gradients"] = complex_gradients
    new_weights = calculate_new_weights(old_complex_weights_path, \
        new_weights_path, lr=0.01)
    
    new_expected_weights = read_compiled_weights(new_complex_weights_path)
    new_actual_weights = read_compiled_weights(new_weights_path)

    for new_weight, new_expected_weight, new_actual_weight \
            in zip(new_weights, new_expected_weights, new_actual_weights):
        assert np.allclose(new_weight, new_expected_weight), \
            "Weights not read correctly!"
        assert np.allclose(new_actual_weight, new_expected_weight), \
            "Weights not written correctly!"