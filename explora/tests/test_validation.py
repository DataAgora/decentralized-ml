import context

import pytest

from utils.validation import validate_repo_id, validate_model, \
    validate_and_prepare_hyperparameters, validate_percentage_averaged, \
    validate_max_rounds, validate_library_type, \
    validate_checkpoint_frequency

def test_repo_id_validation(good_repo_id, bad_repo_id):
    """
    Test that a valid repo ID passes validation and an invalid one fails
    validation.
    """
    assert validate_repo_id(good_repo_id), \
        "This repo ID should have passed validation!"

    assert not validate_repo_id(bad_repo_id), \
        "This repo ID should have failed validation!"

def test_keras_model_validation(good_keras_model, bad_keras_model):
    """
    Test that a valid Keras model passes validation and an invalid one fails 
    validation.
    """
    assert validate_model(good_keras_model), \
        "This repo ID should have passed validation!"

    assert not validate_model(bad_keras_model), \
        "This repo ID should have failed validation!"

def test_hyperparams_validation(good_hyperparams, bad_hyperparams):
    """
    Test that valid hyperparams pass validation and invalid ones fail 
    validation.
    """
    assert validate_and_prepare_hyperparameters(good_hyperparams), \
        "This repo ID should have passed validation!"

    assert not validate_and_prepare_hyperparameters(bad_hyperparams), \
        "This repo ID should have failed validatopm!"

def test_percentage_averaged_validation(good_percentage_averaged, \
        bad_percentage_averaged):
    """
    Test that a valid percentage averaged passes validation and an invalid one
    fails validation.
    """
    assert validate_percentage_averaged(good_percentage_averaged), \
        "This repo ID should have passed validation!"

    assert not validate_percentage_averaged(bad_percentage_averaged), \
        "This repo ID should have failed validatopm!"

def test_max_rounds_validation(good_max_rounds, bad_max_rounds):
    """
    Test that a valid max rounds passes validation and an invalid one fails 
    validation.
    """
    assert validate_max_rounds(good_max_rounds), \
        "This repo ID should have passed validation!"

    assert not validate_max_rounds(bad_max_rounds), \
        "This repo ID should have failed validatopm!"

def test_library_type_validation(good_library_type, bad_library_type):
    """
    Test that a valid library type passes validation and an invalid one fails
    validation.
    """
    assert validate_library_type(good_library_type), \
        "This repo ID should have passed validation!"

    assert not validate_library_type(bad_library_type), \
        "This repo ID should have failed validatopm!"

def test_checkpoint_frequency_validation(good_checkpoint_frequency, \
        bad_checkpoint_frequency, good_max_rounds):
    """
    Test that a valid checkpoint frequency passes validation and an invalid 
    one fails validation.
    """
    assert validate_checkpoint_frequency(good_checkpoint_frequency, \
        good_max_rounds), "This repo ID should have passed validation!"

    assert not validate_checkpoint_frequency(bad_checkpoint_frequency, \
        good_max_rounds), "This repo ID should have failed validation!"