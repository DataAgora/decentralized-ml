import uuid

import tensorflow as tf
tf.compat.v1.disable_v2_behavior()

from utils.validation import valid_repo_id, valid_model, \
    valid_and_prepare_hyperparameters, valid_percentage_averaged, \
    valid_max_rounds, valid_library_type, \
    valid_checkpoint_frequency
from utils.s3_utils import upload_keras_model
from utils.websocket_utils import websocket_connect
from utils.enums import ErrorMessages, data_types
from utils.data_config import DataConfig, ImageConfig 


CLOUD_BASE_URL = ".au4c4pd2ch.us-west-1.elasticbeanstalk.com"

def make_data_config(data_type, class_labels, color_space=None, \
        image_dims=None):
    assert data_type in data_types, ErrorMessages.INVALID_DATA_TYPE.value
    return ImageConfig(class_labels, color_space, image_dims)

async def start_new_session(repo_id, model, hyperparameters, \
        percentage_averaged=0.75, max_rounds=5, library_type="PYTHON", \
        checkpoint_frequency=1, data_config=None):
    """
    valid arguments and then start a new session by sending a message to
    the server with the given configuration. Designed to be called in
    `Explora.ipynb`.

    Args:
        repo_id (str): The repo ID associated with the current dataset.
        model (keras.engine.Model): The initial Keras model to train with. The
            model must be compiled!
        hyperparams (dict): The hyperparameters to be used during training.
            Must include `batch_size`!
        percentage_averaged (float): Percentage of nodes to be averaged before
            moving on to the next round.
        max_rounds (int): Maximum number of rounds to train for.
        library_type (str): The type of library to train with. Must be either
            `PYTHON` or `JAVASCRIPT`.
        checkpoint_frequency (int): Save the model in S3 every
            `checkpoint_frequency` rounds.
        data_config (dict): The configuration for the dataset, if applicable.
            If `library_type` is `IOS`, then this argument is required!  

    Examples:
        >>> start_new_session(
        ...     repo_id="c9bf9e57-1685-4c89-bafb-ff5af830be8a",
        ...     model=keras.models.load_model("model.h5"),
        ...     hyperparameters={"batch_size": 100},
        ...     percentage_averaged=0.75,
        ...     max_rounds=5,
        ...     library_type="PYTHON",
        ...     checkpoint_frequency=1,
        ... )
        Starting session!
        Waiting...
        Session complete! Check dashboard for final model!
    """
    cloud_node_host = "ws://" + repo_id + CLOUD_BASE_URL
    session_id = str(uuid.uuid4())

    if not (valid_repo_id(repo_id) \
            and valid_library_type(library_type) \
            and valid_model(model, library_type) \
            and valid_and_prepare_hyperparameters(hyperparameters) \
            and valid_percentage_averaged(percentage_averaged) \
            and valid_max_rounds(max_rounds) \
            and valid_checkpoint_frequency(checkpoint_frequency, max_rounds) \
            and valid_data_config(library_type, data_config)):
        return

    h5_model_path = "model/model.h5"
    model.save(h5_model_path)
    if not upload_keras_model(repo_id, session_id, h5_model_path):
        print("Model upload failed!")
        return

    new_message = {
        "type": "NEW_SESSION",
        "session_id": session_id,
        "repo_id": repo_id,
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
        "library_type": library_type
    }

    await websocket_connect(cloud_node_host, new_message)