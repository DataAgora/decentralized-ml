import context

import pytest

from explora import make_data_config
from utils.validation import valid_repo_id, valid_model, \
    valid_and_prepare_hyperparameters, valid_percentage_averaged, \
    valid_max_rounds, valid_library_type, valid_dataset_id, \
    valid_checkpoint_frequency, valid_data_config, valid_image_config_args, \
    valid_text_config_args, valid_session_args, valid_model_name
from utils.enums import ModelPaths


def test_repo_id_validation(good_repo_id, bad_repo_id):
    """
    Test that a valid repo ID passes validation and an invalid one fails
    validation.
    """
    assert valid_repo_id(good_repo_id), \
        "This repo ID should have passed validation!"

    assert not valid_repo_id(bad_repo_id), \
        "This repo ID should have failed validation!"

def test_dataset_id_validation(ios, python, good_dataset_id, bad_dataset_id):
    """
    Test that a valid dataset ID passes validation and an invalid one fails
    validation.
    """
    assert valid_dataset_id(ios, good_dataset_id), \
        "This repo ID should have passed validation!"

    assert not valid_dataset_id(ios, bad_dataset_id), \
        "This repo ID should have failed validation!"

    assert valid_dataset_id(python, None), \
        "This repo ID should have passed validation!"

    assert not valid_dataset_id(python, good_dataset_id), \
        "This repo ID should have failed validation!"

def test_keras_validation(good_keras_path, bad_keras_path):
    """
    Test that a valid Keras model passes validation and an invalid one fails 
    validation.
    """
    assert valid_model(None, good_keras_path), \
        "This model path should have passed validation!"

    assert not valid_model(None, bad_keras_path), \
        "This model path should have failed validation!"

    assert not valid_model(None, ""), \
        "This model path should have failed validation!"

def test_ios_model_validation(good_image_config, good_ios_model_path, \
        bad_ios_model_path, bad_ios_model_path_2):
    """
    Test that a valid Keras model for iOS passes validation and an invalid one 
    fails validation.
    """
    assert valid_model(good_image_config, good_ios_model_path), \
        "This model path should have passed validation!"

    assert not valid_model(good_image_config, bad_ios_model_path), \
        "This model path should have failed validation!"

    assert not valid_model(good_image_config, bad_ios_model_path_2), \
        "This model path should have failed validation!"

    assert not valid_model(good_image_config, None), \
        "This model path should have failed validation!"

def test_mlmodel_validation(good_text_config, good_mlmodel_path):
    """
    Test that a valid MLModel for iOS passes validation and an invalid one 
    fails validation.
    """
    assert valid_model(good_text_config, good_mlmodel_path), \
        "This model path should have passed validation!"

    assert not valid_model(good_text_config, None), \
        "This model path should have failed validation!"

def test_model_name(python, good_keras_name, ios, mnist_config, \
        good_mlmodel_name, ngram_config, bad_model_name, good_keras_path):
    """
    Test that a valid model name passes validation and an invalid one fails 
    validation.
    """
    model_path, data_config = valid_model_name(good_keras_name, python, None)
    assert model_path == ModelPaths.MNIST_PATH.value and not data_config, \
        "This model name should have passed validation!"

    model_path, data_config = valid_model_name(good_keras_name, ios, None)
    assert model_path == ModelPaths.IOS_MNIST_PATH.value \
            and data_config == mnist_config, \
        "This model name should have passed validation!"

    model_path, data_config = valid_model_name(good_mlmodel_name, ios, None)
    assert model_path == ModelPaths.NGRAM_PATH.value \
            and data_config == ngram_config, \
        "This model name should have passed validation!"

    model_path, data_config = valid_model_name(bad_model_name, python, None)
    assert not model_path and not data_config, \
        "This model name should have failed validation!"

    model_path, data_config = valid_model_name(good_keras_name, python, \
        good_keras_path)
    assert not model_path and not data_config, \
        "This model name should have failed validation!"

def test_hyperparams_validation(good_hyperparams, bad_hyperparams):
    """
    Test that valid hyperparams pass validation and invalid ones fail 
    validation.
    """
    assert valid_and_prepare_hyperparameters(good_hyperparams), \
        "These hyperparameters should have passed validation!"

    assert not valid_and_prepare_hyperparameters(bad_hyperparams), \
        "These hyperparameters should have failed validation!"

def test_percentage_averaged_validation(good_percentage_averaged, \
        bad_percentage_averaged):
    """
    Test that a valid percentage averaged passes validation and an invalid one
    fails validation.
    """
    assert valid_percentage_averaged(good_percentage_averaged), \
        "This percentage averaged should have passed validation!"

    assert not valid_percentage_averaged(bad_percentage_averaged), \
        "This percentage averaged should have failed validation!"

def test_max_rounds_validation(good_max_rounds, bad_max_rounds):
    """
    Test that a valid max rounds passes validation and an invalid one fails 
    validation.
    """
    assert valid_max_rounds(good_max_rounds), \
        "This max rounds should have passed validation!"

    assert not valid_max_rounds(bad_max_rounds), \
        "This max rounds should have failed validation!"

def test_library_type_validation(good_library_type, bad_library_type):
    """
    Test that a valid library type passes validation and an invalid one fails
    validation.
    """
    assert valid_library_type(good_library_type), \
        "This library type should have passed validation!"

    assert not valid_library_type(bad_library_type), \
        "This library type should have failed validation!"

def test_checkpoint_frequency_validation(good_checkpoint_frequency, \
        bad_checkpoint_frequency, good_max_rounds):
    """
    Test that a valid checkpoint frequency passes validation and an invalid 
    one fails validation.
    """
    assert valid_checkpoint_frequency(good_checkpoint_frequency, \
            good_max_rounds), \
        "This checkpoint frequency should have passed validation!"

    assert not valid_checkpoint_frequency(bad_checkpoint_frequency, \
            good_max_rounds), \
        "This checkpoint frequency should have failed validation!"

def test_data_config(ios, python, good_image_config, good_text_config):
    """
    Test that a valid data config passes validation and an invalid one fails
    validation.
    """
    assert valid_data_config(ios, good_image_config), \
        "This image config should have passed validation!"

    assert valid_data_config(ios, good_text_config), \
        "This text config should have passed validation!"

    assert not valid_data_config(ios, None), \
        "This data config should have failed validation!"

    assert valid_data_config(python, None), \
        "This data config should have passed validation!"

    assert not valid_data_config(python, good_image_config), \
        "This data config should have failed validation!"

def test_image_config(good_image_config_args, bad_image_config_args, \
        bad_image_config_args_2, bad_image_config_args_3):
    """
    Test that valid image arguments pass validation and invalid ones fail 
    validation.
    """
    assert valid_image_config_args(*good_image_config_args), \
        "These image args should have passed validation!"
    
    assert not valid_image_config_args(*bad_image_config_args), \
        "These image args should have failed validation!"

    assert not valid_image_config_args(*bad_image_config_args_2), \
        "These image args should have failed validation!"

    assert not valid_image_config_args(*bad_image_config_args_3), \
        "These image args should have failed validation!"

def test_text_config(good_text_config_args, bad_text_config_args):
    """
    Test that valid image arguments pass validation and invalid ones fail 
    validation.
    """
    assert valid_text_config_args(*good_text_config_args), \
        "These text args should have passed validation!"
    
    assert not valid_text_config_args(*bad_text_config_args), \
        "These text args should have failed validation!"

def test_make_config_assertion(bad_data_type, good_image_labels):
    """
    Test that trying to make an image config with an invalid data type will
    raise an AssertionError.
    """
    with pytest.raises(AssertionError):
        make_data_config(bad_data_type, good_image_labels)
