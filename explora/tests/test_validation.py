import context

import pytest

from utils.validation import valid_repo_id, valid_model, \
    valid_and_prepare_hyperparameters, valid_percentage_averaged, \
    valid_max_rounds, valid_library_type, \
    valid_checkpoint_frequency

def test_repo_id_validation(good_repo_id, bad_repo_id):
    """
    Test that a valid repo ID passes validation and an invalid one fails
    validation.
    """
    assert valid_repo_id(good_repo_id), \
        "This repo ID should have passed validation!"

    assert not valid_repo_id(bad_repo_id), \
        "This repo ID should have failed validation!"

def test_keras_model_validation(good_keras_model, bad_keras_model):
    """
    Test that a valid Keras model passes validation and an invalid one fails 
    validation.
    """
    assert valid_model(good_keras_model), \
        "This repo ID should have passed validation!"

    assert not valid_model(bad_keras_model), \
        "This repo ID should have failed validation!"

def test_hyperparams_validation(good_hyperparams, bad_hyperparams):
    """
    Test that valid hyperparams pass validation and invalid ones fail 
    validation.
    """
    assert valid_and_prepare_hyperparameters(good_hyperparams), \
        "This repo ID should have passed validation!"

    assert not valid_and_prepare_hyperparameters(bad_hyperparams), \
        "This repo ID should have failed validatopm!"

def test_percentage_averaged_validation(good_percentage_averaged, \
        bad_percentage_averaged):
    """
    Test that a valid percentage averaged passes validation and an invalid one
    fails validation.
    """
    assert valid_percentage_averaged(good_percentage_averaged), \
        "This repo ID should have passed validation!"

    assert not valid_percentage_averaged(bad_percentage_averaged), \
        "This repo ID should have failed validatopm!"

def test_max_rounds_validation(good_max_rounds, bad_max_rounds):
    """
    Test that a valid max rounds passes validation and an invalid one fails 
    validation.
    """
    assert valid_max_rounds(good_max_rounds), \
        "This repo ID should have passed validation!"

    assert not valid_max_rounds(bad_max_rounds), \
        "This repo ID should have failed validatopm!"

def test_library_type_validation(good_library_type, bad_library_type):
    """
    Test that a valid library type passes validation and an invalid one fails
    validation.
    """
    assert valid_library_type(good_library_type), \
        "This repo ID should have passed validation!"

    assert not valid_library_type(bad_library_type), \
        "This repo ID should have failed validatopm!"

def test_checkpoint_frequency_validation(good_checkpoint_frequency, \
        bad_checkpoint_frequency, good_max_rounds):
    """
    Test that a valid checkpoint frequency passes validation and an invalid 
    one fails validation.
    """
    assert valid_checkpoint_frequency(good_checkpoint_frequency, \
        good_max_rounds), "This repo ID should have passed validation!"

    assert not valid_checkpoint_frequency(bad_checkpoint_frequency, \
        good_max_rounds), "This repo ID should have failed validation!"