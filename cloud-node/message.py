import json
import base64
from enum import Enum

import numpy as np

class MessageType(Enum):
    """
    Message Type

    Message Types that the service can work with.

    """

    REGISTER = "REGISTER"
    NEW_SESSION = "NEW_SESSION"
    NEW_WEIGHTS = "NEW_WEIGHTS"


class Message:
    """
    Message

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
    Registration Message

    The type of message initially sent by a node with information of what type
    of node they are.

    `node_type` should be one of DASHBOARD or LIBRARY.

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
    New Session Message

    The type of message sent by Explora to start a new session.

    """

    type = MessageType.NEW_SESSION.value

    def __init__(self, serialized_message):
        self.repo_id = serialized_message["repo_id"]
        self.h5_model = serialized_message["h5_model"]
        self.hyperparams = serialized_message["hyperparams"]
        self.selection_criteria = serialized_message["selection_criteria"]
        self.continuation_criteria = serialized_message["continuation_criteria"]
        self.termination_criteria = serialized_message["termination_criteria"]

    def __repr__(self):
        return json.dumps({
            "repo_id": self.repo_id,
            "h5_model": self.h5_model[:20],
            "hyperparams": self.hyperparams,
            "selection_criteria": self.selection_criteria,
            "continuation_criteria": self.continuation_criteria,
            "termination_criteria": self.termination_criteria,
        })


class NewWeightsMessage(Message):
    """
    New Weights Message

    The type of message sent by the Library. This is an update.

    """

    type = MessageType.NEW_WEIGHTS.value

    def __init__(self, serialized_message):
        self.session_id = serialized_message["session_id"]
        self.round = serialized_message["round"]
        self.action = serialized_message["action"]
        self.weights = np.array(
            serialized_message["results"]["weights"],
            dtype=np.dtype(float),
        )
        self.omega = serialized_message["results"]["omega"]

    def __repr__(self):
        return json.dumps({
            "session_id": self.session_id,
            "round": self.round,
            "action": self.action,
            "weights": "omitted",
            "omega": self.omega,
        })
