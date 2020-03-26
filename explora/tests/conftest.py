import context

import pytest
import keras
import tensorflow as tf
tf.compat.v1.disable_v2_behavior()

from explora import make_data_config
from utils.enums import LibraryType, ModelNames
from utils.validation import _make_mnist_config, _make_ngram_config


@pytest.fixture(scope="session")
def good_repo_id():
    return "99885f00eefcd4107572eb62a5cb429a"

@pytest.fixture(scope="session")
def bad_repo_id():
    return "bad_repo_id"

@pytest.fixture(scope="session")
def good_dataset_id():
    return "testDataset"

@pytest.fixture(scope="session")
def bad_dataset_id():
    return None

@pytest.fixture(scope="session")
def good_keras_path():
    return "explora/tests/artifacts/model.h5"

@pytest.fixture(scope="session")
def good_ios_model_path():
    return "explora/tests/artifacts/ios_model.h5"

@pytest.fixture(scope="session")
def bad_keras_path():
    return "explora/tests/artifacts/bad_model.h5"

@pytest.fixture(scope="session")
def bad_ios_model_path():
    return "explora/tests/artifacts/bad_ios_model.h5"

@pytest.fixture(scope="session")
def bad_ios_model_path_2():
    return "explora/tests/artifacts/bad_ios_model_2.h5"

@pytest.fixture(scope="session")
def good_mlmodel_path():
    return "explora/tests/artifacts/my_model.mlmodel"

@pytest.fixture(scope="session")
def good_keras_name():
    return ModelNames.MNIST.value

@pytest.fixture(scope="session")
def good_mlmodel_name():
    return ModelNames.NGRAM.value

@pytest.fixture(scope="session")
def bad_model_name():
    return "bad-model-name"

@pytest.fixture(scope="session")
def good_hyperparams():
    return {
        "batch_size": 100,
    }

@pytest.fixture(scope="session")
def bad_hyperparams():
    return {
        "batch_size": -1,
    }

@pytest.fixture(scope="session")
def good_percentage_averaged():
    return 0.75

@pytest.fixture(scope="session")
def bad_percentage_averaged():
    return 2

@pytest.fixture(scope="session")
def good_max_rounds():
    return 5

@pytest.fixture(scope="session")
def bad_max_rounds():
    return 0

@pytest.fixture(scope="session")
def python():
    return LibraryType.PYTHON.value

@pytest.fixture(scope="session")
def ios():
    return LibraryType.IOS.value

@pytest.fixture(scope="session")
def good_library_type(python):
    return python

@pytest.fixture(scope="session")
def bad_library_type():
    return "JAVA"

@pytest.fixture(scope="session")
def good_checkpoint_frequency():
    return 1

@pytest.fixture(scope="session")
def bad_checkpoint_frequency():
    return -1

@pytest.fixture(scope="session")
def image():
    return "image"

@pytest.fixture(scope="session")
def text():
    return "text"

@pytest.fixture(scope="session")
def bad_data_type():
    return "bad_type"

@pytest.fixture(scope="session")
def good_image_labels():
    return ["label1", "label2"]

@pytest.fixture(scope="session")
def bad_image_labels():
    return "label"

@pytest.fixture(scope="session")
def good_color_space():
    return "GRAYSCALE"

@pytest.fixture(scope="session")
def bad_color_space():
    return "BLUE"

@pytest.fixture(scope="session")
def good_image_dims():
    return (5, 5)

@pytest.fixture(scope="session")
def bad_image_dims():
    return (5.4, 7.7)

@pytest.fixture(scope="session")
def good_vocab_size():
    return 100

@pytest.fixture(scope="session")
def bad_vocab_size():
    return 0

@pytest.fixture(scope="session")
def good_image_config(image, good_image_labels, good_color_space, \
        good_image_dims):
    return make_data_config(
        data_type=image, 
        image_labels=good_image_labels, 
        color_space=good_color_space,
        dims=good_image_dims
    )

@pytest.fixture(scope="session")
def good_text_config(text, good_vocab_size):
    return make_data_config(
        data_type=text, 
        vocab_size=good_vocab_size
    )

@pytest.fixture(scope="session")
def good_image_config_args(good_image_labels, good_color_space, \
        good_image_dims):
    return (good_image_labels, good_color_space, good_image_dims)

@pytest.fixture(scope="session")
def bad_image_config_args(bad_image_labels, good_color_space, \
        good_image_dims):
    return (bad_image_labels, good_color_space, good_image_dims)

@pytest.fixture(scope="session")
def bad_image_config_args_2(good_image_labels, bad_color_space, \
        good_image_dims):
    return (good_image_labels, bad_color_space, good_image_dims)

@pytest.fixture(scope="session")
def bad_image_config_args_3(good_image_labels, good_color_space, \
        bad_image_dims):
    return (good_image_labels, good_color_space, bad_image_dims)

@pytest.fixture(scope="session")
def good_text_config_args(good_vocab_size):
    return (good_vocab_size,) 

@pytest.fixture(scope="session")
def bad_text_config_args(bad_vocab_size):
    return (bad_vocab_size,) 

@pytest.fixture(scope="session")
def mnist_config():
    return _make_mnist_config()

@pytest.fixture(scope="session")
def ngram_config():
    return _make_ngram_config()
  