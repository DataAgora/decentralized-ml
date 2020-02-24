import context

import pytest
import keras
import tensorflow as tf
tf.compat.v1.disable_v2_behavior()

from explora import make_data_config


@pytest.fixture(scope="session")
def good_repo_id():
    return "99885f00eefcd4107572eb62a5cb429a"

@pytest.fixture(scope="session")
def bad_repo_id():
    return "bad_repo_id"

@pytest.fixture(scope="session")
def good_keras_model():
    return keras.models.load_model("explora/tests/artifacts/model.h5")

@pytest.fixture(scope="session")
def good_keras_ios_model():
    return keras.models.load_model("explora/tests/artifacts/ios_model.h5")

@pytest.fixture(scope="session")
def bad_keras_model():
    model = keras.models.load_model("explora/tests/artifacts/model.h5")
    model.optimizer = None
    return model

@pytest.fixture(scope="session")
def bad_keras_ios_model():
    model = keras.models.load_model("explora/tests/artifacts/ios_model.h5")
    model.loss = keras.losses.sparse_categorical_crossentropy
    return model

@pytest.fixture(scope="session")
def bad_keras_ios_model_2():
    model = keras.models.load_model("explora/tests/artifacts/ios_model.h5")
    model.loss = keras.optimizers.RMSprop()
    return model

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
def good_library_type():
    return "PYTHON"

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
def good_data_type():
    return "image"

@pytest.fixture(scope="session")
def bad_data_type():
    return "text"

@pytest.fixture(scope="session")
def good_class_labels():
    return ["label1", "label2"]

@pytest.fixture(scope="session")
def bad_class_labels():
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
def good_image_config(good_data_type, good_class_labels, good_color_space, \
        good_image_dims):
    return make_data_config(
        data_type=good_data_type, 
        class_labels=good_class_labels, 
        color_space=good_color_space, 
        image_dims=good_image_dims
    )

@pytest.fixture(scope="session")
def bad_image_config():
    return None  

@pytest.fixture(scope="session")
def bad_image_config_2(good_data_type, bad_class_labels, good_color_space, \
        good_image_dims):
    return make_data_config(
        data_type=good_data_type, 
        class_labels=bad_class_labels, 
        color_space=good_color_space, 
        image_dims=good_image_dims
    )

@pytest.fixture(scope="session")
def bad_image_config_3(good_data_type, good_class_labels, bad_color_space, \
        good_image_dims):
    return make_data_config(
        data_type=good_data_type, 
        class_labels=good_class_labels, 
        color_space=bad_color_space, 
        image_dims=good_image_dims
    )

@pytest.fixture(scope="session")
def bad_image_config_4(good_data_type, good_class_labels, good_color_space, \
        bad_image_dims):
    return make_data_config(
        data_type=good_data_type, 
        class_labels=good_class_labels, 
        color_space=good_color_space, 
        image_dims=bad_image_dims
    )
  