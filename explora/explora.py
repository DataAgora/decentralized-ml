import uuid

from utils.validation import validate_repo_id, validate_model, \
    validate_and_prepare_hyperparameters, validate_percentage_averaged, \
    validate_max_rounds, validate_library_type, \
    validate_checkpoint_frequency
from utils.s3_utils import upload_keras_model
from utils.websocket_utils import connect


async def start_new_session(self, repo_id, model, hyperparameters, \
        percentage_averaged=0.75, max_rounds=5, library_type="PYTHON", \
        checkpoint_frequency=1):
    """
    Validate arguments and then start a new session by sending a message to 
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
    cloud_node_host = "ws://" + repo_id + self.CLOUD_BASE_URL
    session_id = str(uuid.uuid4())

    if not validate_repo_id(repo_id):
        print("Repo ID is not in a valid format!")
        return

    if not validate_model(model):
        print("Provided model is not a Keras model!")
        return

    if not validate_and_prepare_hyperparameters(hyperparameters):
        print("Hyperparameters must include batch size!")
        return

    if not validate_percentage_averaged(percentage_averaged):
        print("Percentage averaged must be float and between 0 and 1!")
        return

    if not validate_max_rounds(max_rounds):
        print("Max rounds must be int and at least 1!")
        return
    
    if not validate_library_type(library_type):
        print("Library type must be either PYTHON or JAVASCRIPT")
        return

    if not validate_checkpoint_frequency(checkpoint_frequency):
        print("Checkpoint frequency must be int and between 0 and max rounds!")
        return

    if not upload_keras_model(repo_id, session_id. h5_model_path):
        print("Model upload failed!")
        return

    new_message = {
        "type": "NEW_SESSION",
        "session_id": session_id,
        "repo_id": repo_id,
        "hyperparams": hyperparams,
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

    await self._connect(new_message)