import uuid

import keras


def validate_repo_id(repo_id):
    """
    Check that repo ID is in the uuid4 format.
    Args:
        repo_id (str): The repo ID associated with the current dataset.
    Returns:
        bool: True if in valid format, False otherwise
    """
    try:
        uuid_obj = uuid.UUID(repo_id, version=4)
    except ValueError:
        return False

    return True

def validate_model(model):
    """
    Check that the model is a Keras model and is compiled.
    Args:
        model (keras.engine.Model): The initial Keras model to train with. The
            model must be compiled!
    Returns:
        bool: True if Keras model and compiled, False otherwise
    """
    return isinstance(model, keras.engine.Model) and model.optimizer

def validate_and_prepare_hyperparameters(hyperparams):
    """
    Check that hyperparams has `batch_size` entry and that it is an 
    appropriate number. Then add default entries for `epochs` and `shuffle`.
    Args:
        hyperparams (dict): The hyperparameters to be used during training. 
            Must include `batch_size`!
    """
    if not isinstance(hyperparams, dict) \
            or hyperparams.get('batch_size', 0) < 1:
        return False
    hyperparams['epochs'] = hyperparams.get('epochs', 5)
    hyperparams['shuffle'] = hyperparams.get('shuffle', True)
    return True

def validate_percentage_averaged(percentage_averaged):
    """
    Check that percentage averaged is 1 OR is float and between 0 and 1.
    Args:
        percentage_averaged (float): Percentage of nodes to be averaged before
            moving on to the next round.
    """
    return percentage_averaged == 1 \
        or (isinstance(percentage_averaged, float) \
            and percentage_averaged > 0 \
            and percentage_averaged < 1)

def validate_max_rounds(max_rounds):
    """
    Check that max rounds is int and at least 1.
    Args:
        max_rounds (int): Maximum number of rounds to train for.
    """
    return isinstance(max_rounds, int) and max_rounds >= 1

def validate_library_type(library_type):
    """
    Check that library_type is PYTHON or JAVASCRIPT.
    Args:
        library_type (str): The type of library to train with. Must be either
            `PYTHON` or `JAVASCRIPT`.
    """
    return library_type in ("PYTHON", "JAVASCRIPT")

def validate_checkpoint_frequency(checkpoint_frequency, max_rounds):
    """
    Check that checkpoint frequency is int and between 0 and max rounds.
    Args:
        checkpoint_frequency (int): Save the model in S3 every 
            `checkpoint_frequency` rounds.
    """
    return isinstance(checkpoint_frequency, int) \
        and checkpoint_frequency >= 1 \
        and checkpoint_frequency <= max_rounds