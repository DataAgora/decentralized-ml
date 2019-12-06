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

class LibraryType(Enum):
    """
    Library Types that the service can work with.
    """
    PYTHON = "PYTHON"
    JS = "JAVASCRIPT"


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

    def __repr__(self):
        return json.dumps({
            "node_type": self.node_type
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
        self.session_id = serialized_message["session_id"]
        self.hyperparams = serialized_message["hyperparams"]
        self.selection_criteria = serialized_message["selection_criteria"]
        self.continuation_criteria = serialized_message["continuation_criteria"]
        self.termination_criteria = serialized_message["termination_criteria"]
        self.library_type = serialized_message["library_type"]
        self.checkpoint_frequency = serialized_message.get("checkpoint_frequency", 1)
        self.node_type = "DASHBOARD"

    def __repr__(self):
        return json.dumps({
            "repo_id": self.repo_id,
            "h5_model": self.h5_model[:20],
            "hyperparams": self.hyperparams,
            "selection_criteria": self.selection_criteria,
            "continuation_criteria": self.continuation_criteria,
            "termination_criteria": self.termination_criteria,
        })


class NewUpdateMessage(Message):
    """
    The type of message sent by the Library. This is an update.

    Args:
        serialized_message (dict): The serialized message to provide the new
            update.
    """
    type = MessageType.NEW_UPDATE.value

    def __init__(self, serialized_message):
        self.session_id = serialized_message["session_id"]
        self.round = serialized_message["round"]
        self.action = serialized_message["action"]
        if "gradients" in serialized_message["results"]:
            gradients = serialized_message["results"]["gradients"]
            self.gradients = [np.array(gradient) for gradient in gradients]
        elif "weights" in serialized_message["results"]:
            self.weights = np.array(
                serialized_message["results"]["weights"],
                dtype=np.dtype(float),
            )
        else:
            raise Exception(("No update received!"))
        self.omega = serialized_message["results"]["omega"]
        self.node_type = "LIBRARY"

    def __repr__(self):
        return json.dumps({
            "session_id": self.session_id,
            "round": self.round,
            "action": self.action,
            "weights": "omitted",
            "omega": self.omega,
        })
