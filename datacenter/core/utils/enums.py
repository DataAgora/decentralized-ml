"""This file contains all the different enums used to implement callback
pattern functionality."""

from enum import Enum

class JobTypes(Enum):
    """
    The different DML Job types used throughout the service.

    The types can be the following:

        JOB_TRAIN: Train a model.

        JOB_VAL: Validate a model.

        JOB_INIT: Initialize a model.

        JOB_AVG: Average weights via weighted average.

        JOB_COMM: Push the weights onto IPFS and then communicate this update
        to rest of the nodes via blockchain.

        JOB_SPLIT: Split the data and put it into new folders.

        JOB_STATS: Submit statistics to a cloud server
        #TODO: Implement transformation of the data
    """
    JOB_TRAIN = "TRAIN"
    JOB_VAL = "VALIDATE"
    JOB_INIT = "INITIALIZE"
    JOB_AVG = "AVERAGE"
    JOB_COMM = "COMMUNICATE"
    JOB_SPLIT = "SPLIT"
    JOB_STATS = "STATISTICS"

class MessageEventTypes(Enum):
    """
    The different Blockchain Message Types used throughout the service.

    The types can be the following:

        NEW_WEIGHTS: New weights from another node.

        TERMINATE: Terminate this session command.

        NEW_SESSION: Information received from the blockchain to create a new
        DML Session.
    """
    NEW_WEIGHTS = "NEW_WEIGHTS"
    TERMINATE = "TERMINATE"
    NEW_SESSION = "NEW_SESSION"

class RawEventTypes(Enum):
    """
    Event types that are not "actionable" by the service in its current form
    (and therefore are "raw"). These events are meant to be transformed by
    something "actionable" by the Optimizer.

    The different Raw Event Types are the following:

        JOB_DONE: Information received from the Scheduler about a job that was
        just completed (in the form of a DML Result).

        NEW_MESSAGE: Information received by the Gateway containing new information
        from the blockchain.
    """
    JOB_DONE = "JOB_DONE"
    NEW_MESSAGE = "NEW_MESSAGE"

class ActionableEventTypes(Enum):
    """
    Actionable event types that the service can take action on.

    The different event types are the following:

        SCHEDULE_JOB: Instruction to the Execution Pipeline to schedule a job
        to run.

        TERMINATE: Instruction to the Communication Manager to terminate a
        DML Session.

        NOTHING: Do nothing; received when new weights were sent to the Optimizer
        or a Communication Job was successfuly received.
    """
    SCHEDULE_JOBS = "SCHEDULE_JOB"
    TERMINATE = "TERMINATE"
    NOTHING = "NOTHING"

class OptimizerTypes(Enum):
    """
    Different types of Optimizers.
    """
    FEDAVG = "FEDERATED_AVERAGING"
    CLOUDCONN = "CLOUD_CONNECTED"

def callback_handler_with_default(callback_type, callback_dict, default="NOTHING"):
    """
    Util function to return a callback from a dictionary that falls back to a
    default callback specified by `default`. The fallback is
    `callback_dict[default]`.
    """
    return _callback_handler(callback_type, callback_dict, True, default)

def callback_handler_no_default(callback_type, callback_dict):
    """
    Util function to return a callback from a dictionary without a fallback
    mechanism. If `callback_type` is not found in `callback_dict` then an
    exception is raised.
    """
    return _callback_handler(callback_type, callback_dict, False)

def _callback_handler(
    callback_type,
    callback_dict,
    with_default=True,
    default="NOTHING",
    ):
    """
    Helper function which returns a callback function from the `callback_dict`
    dictionary.

    The callback_dict dictionary should be a dictionary of strings to functions.

    When `with_default` is True (default), the `callback_dict` should contain
    a key `default` which is the fallback callback returned when `callback_type`
    is not found in `callback_dict`. If False, then the function will raise an
    exception instead of falling back to a default entry.
    """
    assert isinstance(callback_dict, dict), \
        "callback_dict was not a dict, it was: {}".format(type(callback_dict))
    if with_default:
        assert default in callback_dict, \
            "The default callback provided was not found in callback_dict"
        return callback_dict.get(callback_type, callback_dict[default])
    else:
        if callback_type not in callback_dict:
            raise Exception("Invalid callback passed!")
        return callback_dict[callback_type]
