import uuid

import keras
import coremltools

from utils.data_config import DataConfig, ImageConfig, TextConfig
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
    Check that library type is valid.

    Args:
        library_type (str): The type of library to train with. Must be either
            `PYTHON` or `JAVASCRIPT` or `IOS`.

    Returns:
        bool: True if valid, False otherwise.
    """
    return library_type in library_types

def _valid_ios_loss(loss):
    """
    Validate the loss function of the model to be used in the iOS library.
    
    Args:
        loss (function): The loss function of the model.

    Returns:
        bool: True if valid, False otherwise.
    """
    if loss != keras.losses.categorical_crossentropy \
            and loss != keras.losses.mean_squared_error:
        print(ErrorMessages.INVALID_LOSS.value)
        return False
    return True

def _valid_ios_optimizer(optimizer):
    """
    Validate the loss function of the model to be used in the iOS library.
    
    Args:
        optimizer (keras.optimizers.Optimizer): The optimizer of the model.

    Returns:
        bool: True if valid, False otherwise.
    """
    if not isinstance(optimizer, keras.optimizers.SGD) \
            and not isinstance(optimizer, keras.optimizers.Adam):
        print(ErrorMessages.INVALID_OPTIMIZER.value)
        return False 
    return True

def valid_model(data_config, model_path):
    """
    Check that the model is a Keras model and is compiled.

    Args:
        data_config (DataConfig): The configuration for the 
            dataset, if applicable. If `library_type` is `IOS`, then this 
            argument is required!
        model_path (str): The path to the initial model to train with. Must be 
            an `.mlmodel` (`MLModel`) file if the model is a text model for 
            iOS, or a `.h5` (compiled Keras model) file otherwise.
    
    Returns:
        bool: True if Keras model and compiled and valid optimizer/loss, False
            otherwise.
    """
    if isinstance(data_config, TextConfig):
        try:
            mlmodel = coremltools.models.MLModel(model_path)
        except:
            print(ErrorMessages.INVALID_MLMODEL_PATH.value)
            return False
    else:
        try:
            model = keras.models.load_model(model_path)
        except:
            print(ErrorMessages.INVALID_KERAS_MODEL_PATH.value)
            return False

        if not model.optimizer or not model.loss:
            print(ErrorMessages.NOT_COMPILED.value)
            return False
        elif isinstance(data_config, ImageConfig):
            loss = model.loss
            optimizer = model.optimizer
            if isinstance(loss, str):
                loss = keras.losses.get(loss)
            if not _valid_ios_loss(loss) \
                    or not _valid_ios_optimizer(optimizer):
                return False
    return True

def valid_and_prepare_hyperparameters(hyperparams):
    """
    Check that hyperparams has `batch_size` entry and that it is an 
    appropriate number. Then add default entries for `epochs` and `shuffle`.

    Args:
        hyperparams (dict): The hyperparameters to be used during training. 
            Must include `batch_size`!

    Returns:
        bool: True if valid, False otherwise.
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

    Returns:
        bool: True if valid, False otherwise.
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

    Returns:
        bool: True if valid, False otherwise.
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

    Returns:
        bool: True if valid, False otherwise.
    """
    if not isinstance(checkpoint_frequency, int) \
            or checkpoint_frequency < 1 \
            or checkpoint_frequency > max_rounds:
        print(ErrorMessages.INVALID_CHECKPOINT_FREQUENCY.value)
        return False
    return True

def valid_data_config(library_type, data_config):
    """
    Check that the data config is valid if the library type is iOS. Otherwise,
    check to make sure that the data_config is not set (`None`).

    Args:
        library_type (str): The type of library to train with.
        data_config (DataConfig): The data config. Can be `None` if the library
            type is not `IOS`.

    Returns:
        bool: True if valid, False otherwise.
    """
    if library_type != LibraryType.IOS.value:
        if data_config is not None:
            print(ErrorMessages.SET_DATA_CONFIG.value)
            return False
        else:
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
    return True    

def valid_image_config_args(class_labels, color_space, dims):
    """
    Check that the arguments for an image config is valid.

    Args:
        image_config (ImageConfig): The image config.

    Returns:
        bool: True if valid, False otherwise.
    """
    if not isinstance(class_labels, list) \
            or len(class_labels) <= 0:
        print(ErrorMessages.INVALID_CLASS_LABELS.value)
        return False
    elif color_space not in color_spaces:
        print(ErrorMessages.INVALID_COLOR_SPACE.value)
        return False
    elif not isinstance(dims, tuple) \
            or len(dims) != 2 \
            or any([not isinstance(dim, int) for dim in dims]):
        print(ErrorMessages.INVALID_IMAGE_DIMS.value)
        return False
    return True

def valid_text_config_args(vocab_size):
    """
    Check that the arguments for an text config is valid.

    Args:
        text_config (TextConfig): The text config.

    Returns:
        bool: True if valid, False otherwise.
    """
    if not isinstance(vocab_size, int) \
            or vocab_size <= 1:
        print(ErrorMessages.INVALID_VOCAB_SIZE.value)
        return False
    return True

def valid_dataset_id(library_type, dataset_id):
    """
    Check to make sure the dataset_id is set if the library type is `IOS`.
    Otherwise, check to make sure the dataset_id is not set (`None`).
    
    Args:
        library_type (str): The type of library to train with.
        dataset_id (str): The dataset ID of the corresponding dataset in the
            iOS library.
    
    Returns:
        bool: True if valid, False otherwise.
    """
    if library_type == LibraryType.IOS.value:
        if not isinstance(dataset_id, str):
            print(ErrorMessages.MISSING_DATASET_ID.value)
            return False
    elif dataset_id != None:
        print(ErrorMessages.SET_DATASET_ID.value)
        return False
    return True

def valid_session_args(repo_id, model, hyperparameters, \
        percentage_averaged=0.75, max_rounds=5, library_type="PYTHON", \
        checkpoint_frequency=1, data_config=None, dataset_id=None):
    """
    Validate arguments for starting a new session. Print error message message
    if validation failed.

    Args:
        repo_id (str): The repo ID associated with the current dataset.
        model (keras.engine.Model): The initial Keras model to train with. The
            model must be compiled!
        hyperparams (dict): The hyperparameters to be used during training.
            Must include `batch_size`!
        percentage_averaged (float): Percentage of nodes to be 
            averaged before moving on to the next round. Defaults to 0.75.
        max_rounds (int): Maximum number of rounds to train for.
            Defaults to 5.
        library_type (str): The type of library to train with. Must
            be either `PYTHON` or `JAVASCRIPT` or `IOS`. Defaults to `PYTHON`.
        checkpoint_frequency (int): Save the model in S3 every
            `checkpoint_frequency` rounds. Defaults to 1.
        data_config (DataConfig): The configuration for the 
            dataset, if applicable. If `library_type` is `IOS`, then this 
            argument is required!
        dataset_id (str): The dataset ID for the dataset, if
            applicable. If `library_type` is `IOS`, then this argument is 
            required since the application may have multiple datasets!
    """
    return valid_repo_id(repo_id) \
        and valid_library_type(library_type) \
        and valid_data_config(library_type, data_config) \
        and valid_model(data_config, model) \
        and valid_and_prepare_hyperparameters(hyperparameters) \
        and valid_percentage_averaged(percentage_averaged) \
        and valid_max_rounds(max_rounds) \
        and valid_checkpoint_frequency(checkpoint_frequency, max_rounds) \
        and valid_dataset_id(library_type, dataset_id)
    