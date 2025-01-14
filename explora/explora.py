import uuid
import os
import sys
sys.stderr = open(os.devnull, 'w')

import logging
logging.disable(logging.CRITICAL)

from utils.validation import valid_setup, valid_session_args, \
    valid_image_config_args, valid_text_config_args, valid_model_name
from utils.aws_utils import upload_keras_model, get_websocket_url
from utils.websocket_utils import websocket_connect
from utils.enums import ErrorMessages, DataType, data_types
from utils.data_config import DataConfig, ImageConfig, TextConfig 


def make_data_config(data_type, image_labels=None, vocab_size=None, \
        color_space=None, dims=None):
    """
    Helper function to generate the required data config for users running 
    training sessions with the iOS library.
    
    Args:
        data_type (str): The type of data the model will train on. Currently,
            only `image` is supported for the iOS library
        image_labels (list, optional): The list of image possible labels in 
            the dataset. Required for image config.
        vocab_size (int, optional): The size of the vocab set. Required for 
            text config.
        color_space (str, optional): The type of image that is inputted into 
            the model, if applicable. Must be specified if `data_type` is 
            `image`. If specified, must be either `GRAYSCALE` or `COLOR`.
        dims (tuple, optional): The dimensions of image that is inputted
            into the model, if applicable. Must be specified if `data_type` is 
            `image`. Must have a length of 2 (width x height).
    
    Returns:
        DataConfig: Data config to be used when starting a new session.
    """
    assert data_type in data_types, ErrorMessages.INVALID_DATA_TYPE.value
    
    if data_type == DataType.IMAGE.value:
        assert valid_image_config_args(image_labels, color_space, dims), \
            "Invalid image config arguments!"
        return ImageConfig(image_labels, color_space, dims)
    else:
        assert valid_text_config_args(vocab_size), \
            "Invalid text config arguments!"
        return TextConfig(vocab_size)

async def start_new_session(hyperparameters, model_name=None, \
        model_path=None, percentage_averaged=0.75, max_rounds=5, \
        library_type="PYTHON", checkpoint_frequency=1, data_config=None, \
        dataset_id=None):
    """
    Validate arguments and then start a new session by sending a message to
    the server with the given configuration. Designed to be called in
    `Explora.ipynb`.

    Args:
        hyperparams (dict): The hyperparameters to be used during training.
            Must include `batch_size`!
        model_path (str, optional): The path to the initial model to train 
            with. Must be an `.mlmodel` (`MLModel`) file if the model is a 
            text model for iOS, or a `.h5` (compiled Keras model) file 
            otherwise.
        percentage_averaged (float, optional): Percentage of nodes to be 
            averaged before moving on to the next round. Defaults to 0.75.
        max_rounds (int, optional): Maximum number of rounds to train for.
            Defaults to 5.
        library_type (str, optional): The type of library to train with. Must
            be either `PYTHON` or `JAVASCRIPT` or `IOS`. Defaults to `PYTHON`.
        checkpoint_frequency (int, optional): Save the model in S3 every
            `checkpoint_frequency` rounds. Defaults to 1.
        data_config (DataConfig, optional): The configuration for the 
            dataset, if applicable. If `library_type` is `IOS`, then this 
            argument is required!
        dataset_id (str, optional): The dataset ID for the dataset, if
            applicable. If `library_type` is `IOS`, then this argument is 
            required since the application may have multiple datasets!
        model_name (str): The name of the default model to train with, stored
            in Explora already. If valid, the model path and data config
            don't need to be specified with this argument.

    Examples:
        >>> start_new_session(
        ...     {"batch_size": 100},
        ...     model_name="mnist",
        ...     percentage_averaged=0.75,
        ...     max_rounds=5,
        ...     library_type="PYTHON",
        ...     checkpoint_frequency=1,
        ... )
        Starting session!
        Waiting...
        Session complete! Check dashboard for final model!
    """
    if not valid_setup():
        return

    repo_id = os.environ["REPO_ID"]
    api_key = os.environ["API_KEY"]

    websocket_url = get_websocket_url(repo_id)
    if not websocket_url:
        return

    session_id = str(uuid.uuid4())

    if model_name:
        model_path, data_config = valid_model_name(model_name, library_type, \
            model_path)
        if not model_path:
            return

    if not valid_session_args(model_path, hyperparameters, \
            percentage_averaged, max_rounds, library_type, \
            checkpoint_frequency, data_config, dataset_id):
        return
    
    is_mlmodel = isinstance(data_config, TextConfig)

    if not upload_keras_model(repo_id, session_id, model_path, is_mlmodel):
        print("Model upload failed!")
        return

    ios_config = data_config.serialize() if data_config else {}

    registration_message = {
        "type": "REGISTER",
        "node_type": "dashboard",
        "repo_id": repo_id,
        "api_key": api_key,
    }

    new_session_message = {
        "type": "NEW_SESSION",
        "session_id": session_id,
        "repo_id": repo_id,
        "dataset_id": dataset_id,
        "hyperparams": hyperparameters,
        "checkpoint_frequency": checkpoint_frequency,
        "selection_criteria": {
            "type": "ALL_NODES",
        },
        "continuation_criteria": {
            "type": "PERCENTAGE_AVERAGED",
            "value": percentage_averaged
        },
        "termination_criteria": {
            "type": "MAX_ROUND",
            "value": max_rounds
        },
        "library_type": library_type,
        "ios_config": ios_config,
    }

    await websocket_connect(websocket_url, registration_message, \
        new_session_message)