import context

import pytest
import keras
import tensorflow as tf
tf.compat.v1.disable_v2_behavior()

@pytest.fixture(scope='session')
def good_repo_id():
    return "99885f00eefcd4107572eb62a5cb429a"

@pytest.fixture(scope='session')
def bad_repo_id():
    return "bad_repo_id"

@pytest.fixture(scope='session')
def good_keras_model():
    print(tf.__version__, "WAH")
    return keras.models.load_model("explora/tests/artifacts/model.h5")

@pytest.fixture(scope='session')
def bad_keras_model():
    model = keras.models.load_model("explora/tests/artifacts/model.h5")
    model.optimizer = None
    return model

@pytest.fixture(scope='session')
def good_hyperparams():
    return {
        "batch_size": 100,
    }

@pytest.fixture(scope='session')
def bad_hyperparams():
    return {
        "batch_size": -1,
    }

@pytest.fixture(scope='session')
def good_percentage_averaged():
    return 0.75

@pytest.fixture(scope='session')
def bad_percentage_averaged():
    return 2

@pytest.fixture(scope='session')
def good_max_rounds():
    return 5

@pytest.fixture(scope='session')
def bad_max_rounds():
    return 0

@pytest.fixture(scope='session')
def good_library_type():
    return "PYTHON"

@pytest.fixture(scope='session')
def bad_library_type():
    return "JAVA"

@pytest.fixture(scope='session')
def good_checkpoint_frequency():
    return 1

@pytest.fixture(scope='session')
def bad_checkpoint_frequency():
    return -1

