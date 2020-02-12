import uuid

import keras

from utils.data_config import DataConfig, ImageConfig
from utils.enums import ErrorMessages, LibraryType, DataType, library_types, \
    color_spaces, data_types

def valid_repo_id(repo_id):
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
        print(ErrorMessages.INVALID_REPO_ID.value)
        return False
    return True

def valid_library_type(library_type):
    """
    Check that library_type is PYTHON or JAVASCRIPT.
    Args:
        library_type (str): The type of library to train with. Must be either
            `PYTHON` or `JAVASCRIPT`.
    """
    return library_type in library_types

def valid_model(library_type, model):
    """
    Check that the model is a Keras model and is compiled.
    Args:
        model (keras.engine.Model): The initial Keras model to train with. The
            model must be compiled!
    Returns:
        bool: True if Keras model and compiled, False otherwise
    """
    if not isinstance(model, keras.engine.Model):
        print(ErrorMessages.INVALID_MODEL_TYPE.value)
        return False
    elif not model.optimizer or not model.loss:
        print(ErrorMessages.NOT_COMPILED.value)
        return False
    elif library_type == LibraryType.IOS.value \
            and model.loss != 'categorical_crossentropy':
        print(ErrorMessages.INVALID_LOSS.value)
        return False

    return True

def valid_and_prepare_hyperparameters(hyperparams):
    """
    Check that hyperparams has `batch_size` entry and that it is an 
    appropriate number. Then add default entries for `epochs` and `shuffle`.
    Args:
        hyperparams (dict): The hyperparameters to be used during training. 
            Must include `batch_size`!
    """
    if not isinstance(hyperparams, dict) \
            or hyperparams.get('batch_size', 0) < 1:
        print(ErrorMessages.INVALID_HYPERPARAMS.value)
        return False
    hyperparams['epochs'] = hyperparams.get('epochs', 5)
    hyperparams['shuffle'] = hyperparams.get('shuffle', True)
    return True

def valid_percentage_averaged(percentage_averaged):
    """
    Check that percentage averaged is 1 OR is float and between 0 and 1.
    Args:
        percentage_averaged (float): Percentage of nodes to be averaged before
            moving on to the next round.
    """
    if percentage_averaged != 1:
        if not isinstance(percentage_averaged, float) \
                or percentage_averaged < 0 \
                or percentage_averaged > 1:
            print(ErrorMessages.INVALID_PERCENTAGE_AVERAGED.value)
            return False
    return True

def valid_max_rounds(max_rounds):
    """
    Check that max rounds is int and at least 1.
    Args:
        max_rounds (int): Maximum number of rounds to train for.
    """
    if not isinstance(max_rounds, int) or max_rounds < 1:
        print(ErrorMessages.INVALID_MAX_ROUNDS.value)
        return False
    return True

def valid_checkpoint_frequency(checkpoint_frequency, max_rounds):
    """
    Check that checkpoint frequency is int and between 0 and max rounds.
    Args:
        checkpoint_frequency (int): Save the model in S3 every 
            `checkpoint_frequency` rounds.
    """
    if not isinstance(checkpoint_frequency, int) \
            or checkpoint_frequency < 1 \
            or checkpoint_frequency > max_rounds:
        print(ErrorMessages.INVALID_CHECKPOINT_FREQUENCY.value)
        return False
    return True

def valid_data_config(library_type, data_config):
    if library_type != LibraryType.IOS.value:
        return True
    elif data_config == None:
        print(ErrorMessages.DATA_CONFIG_NOT_SPECIFIED.value)
        return False
    elif not isinstance(data_config, DataConfig):
        print(ErrorMessages.UNKNOWN_CONFIG.value)
        return False
    elif data_config.data_type not in data_types:
        print(ErrorMessages.INVALID_DATA_TYPE.value)
        return False
    elif not isinstance(data_config.class_labels, list) \
            or len(data_config.class_labels) > 0:
        print(ErrorMessages.INVALID_CLASS_LABELS.value)
        return False
    elif data_config.data_type == DataType.IMAGE.value \
            and not valid_image_config(data_config):
        return False
    return True    

def valid_image_config(image_config):
    if image_config.color_space not in color_spaces:
        print(ErrorMessages.INVALID_COLOR_SPACE.value)
        return False
    elif not isinstance(image_config.dims, tuple) \
            or len(image_config.dims) != 2 \
            or any([not isinstance(dim, int) for dim in image_config.dims]):
        print(ErrorMessages.INVALID_IMAGE_DIMS.value)
        return False
    return True
    