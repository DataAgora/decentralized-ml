import json
import base64
import numpy as np
from enum import Enum


class MessageType(Enum):
    """
    Message Types that the service can work with.
    """
    REGISTER = "REGISTER"
    NEW_SESSION = "NEW_SESSION"
    NEW_UPDATE = "NEW_UPDATE"
    NO_DATASET = "NO_DATASET"
    TRAINING_ERROR = "TRAINING_ERROR"

class LibraryType(Enum):
    """
    Library Types that the service can work with.
    """
    PYTHON = "PYTHON"
    JS = "JAVASCRIPT"
    IOS = "IOS"
    IOS_IMAGE = "IOS_IMAGE"
    IOS_TEXT = "IOS_TEXT"

class Message:
    """
    Base class for messages received by the service.
    """
    @staticmethod
    def make(serialized_message):
        type, data = serialized_message["type"], serialized_message
        for cls in Message.__subclasses__():
            if cls.type == type:
                return cls(data)
        raise ValueError("Message type is invalid!")


class RegistrationMessage(Message):
    """
    The type of message initially sent by a node with information of what type
    of node they are.

    `node_type` should be one of DASHBOARD or LIBRARY.

    Args:
        serialized_message (dict): The serialized message to register a new
            node.
    """
    type = MessageType.REGISTER.value

    def __init__(self, serialized_message):
        self.node_type = serialized_message["node_type"].upper()
        self.repo_id = serialized_message["repo_id"]
        self.api_key = serialized_message["api_key"]
        if self.node_type == "DASHBOARD":
            self.is_demo = serialized_message["is_demo"]

    def __repr__(self):
        return json.dumps({
            "node_type": self.node_type,
            "repo_id": self.repo_id,
            "api_key": self.api_key, 
        })


class NewSessionMessage(Message):
    """
    The type of message sent by Explora to start a new session.

    Args:
        serialized_message (dict): The serialized message to start a new
            session.
    """

    type = MessageType.NEW_SESSION.value

    def __init__(self, serialized_message):
        self.repo_id = serialized_message["repo_id"]
        self.dataset_id = serialized_message.get("dataset_id", None)
        self.session_id = serialized_message["session_id"]
        self.hyperparams = serialized_message["hyperparams"]
        self.selection_criteria = serialized_message["selection_criteria"]
        self.continuation_criteria = serialized_message["continuation_criteria"]
        self.termination_criteria = serialized_message["termination_criteria"]
        self.checkpoint_frequency = serialized_message.get("checkpoint_frequency", 1)
        self.ios_config = serialized_message["ios_config"]
        self.library_type = serialized_message["library_type"]
        self.node_type = "DASHBOARD"

    def __repr__(self):
        return json.dumps({
            "repo_id": self.repo_id,
            "hyperparams": self.hyperparams,
            "selection_criteria": self.selection_criteria,
            "continuation_criteria": self.continuation_criteria,
            "termination_criteria": self.termination_criteria,
            "checkpoint_frequency": self.checkpoint_frequency,
            "ios_config": self.ios_config,
            "library_type": self.library_type,
        })


class NewUpdateMessage(Message):
    """
    The update message sent by the Library. Indicates new weights or gradients
    to be averaged after training.

    Args:
        serialized_message (dict): The serialized message to provide the new
            update.
    """
    type = MessageType.NEW_UPDATE.value

    def __init__(self, serialized_message):
        self.repo_id = serialized_message["repo_id"]
        self.session_id = serialized_message["session_id"]
        self.round = serialized_message["round"]
        if "gradients" in serialized_message["results"]:
            if isinstance(serialized_message["results"], str):
                serialized_message["results"] = json.loads(serialized_message["results"])
            gradients = serialized_message["results"]["gradients"]
            self.gradients = [np.array(gradient) for gradient in gradients]
            self.binary_weights = serialized_message["results"].get("binary_gradients", None)
        elif "weights" in serialized_message["results"]:
            self.weights = np.array(
                serialized_message["results"]["weights"],
                dtype=np.dtype(float),
            )
        else:
            raise Exception(("No update received!"))
        self.omega = serialized_message["results"]["omega"]
        self.dataset_id = serialized_message.get("dataset_id", None)
        self.node_type = "LIBRARY"

    def __repr__(self):
        return json.dumps({
            "repo_id": self.repo_id,
            "session_id": self.session_id,
            "round": self.round,
            "weights": "omitted",
            "omega": self.omega,
        })

class NoDatasetMessage(Message):
    """
    The no dataset message sent by the Library. Indicates that this client
    does not have the specified dataset.

    Args:
        serialized_message (dict): The serialized message to provide the no
            dataset message.
    """
    type = MessageType.NO_DATASET.value

    def __init__(self, serialized_message):
        self.repo_id = serialized_message["repo_id"]
        self.session_id = serialized_message["session_id"]
        self.round = serialized_message["round"]
        self.dataset_id = serialized_message["dataset_id"]
        self.node_type = "LIBRARY"

    def __repr__(self):
        return json.dumps({
            "repo_id": self.repo_id,
            "session_id": self.session_id,
            "dataset_id": self.dataset_id,
            "round": self.round,
        })

class TrainingErrorMessage(Message):
    """
    The no dataset message sent by the Library. Indicates that this client
    does not have the specified dataset.

    Args:
        serialized_message (dict): The serialized message to provide the no
            dataset message.
    """
    type = MessageType.TRAINING_ERROR.value

    def __init__(self, serialized_message):
        self.repo_id = serialized_message["repo_id"]
        self.session_id = serialized_message["session_id"]
        self.round = serialized_message["round"]
        self.dataset_id = serialized_message["dataset_id"]
        self.node_type = "LIBRARY"

    def __repr__(self):
        return json.dumps({
            "repo_id": self.repo_id,
            "session_id": self.session_id,
            "dataset_id": self.dataset_id,
            "round": self.round,
        })