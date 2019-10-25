import uuid
import os
import json
import io

import numpy as np
import keras

from custom.keras import model_from_serialized
from core.utils.filesys import ensure_dir
import logging 

logger = logging.getLogger('Utils/Keras')
# import logging as utils_logging

# utils_logging.basicConfig(level=utils_logging.INFO,
#                     format='[Utils/Keras] %(asctime)s %(levelname)s %(message)s')

def train_keras_model(model, dataset_iterator, data_count,
    hyperparams, config):
    logger.info('Keras training just started.')
    print(data_count, hyperparams['batch_size'])
    hist = model.fit_generator(dataset_iterator, epochs=hyperparams['epochs'], \
        steps_per_epoch=data_count//hyperparams['batch_size'])
    # weights_filepath = os.path.join(
    #     os.path.dirname(os.path.realpath(__file__)),
    #     config["weights_directory"],
    #     uuid.uuid4().hex[:8] + ".h5"
    # )
    # ensure_dir(weights_filepath)
    # model.save_weights(weights_filepath)
    # weights = model.get_weights()
    logger.info('Keras training complete.')
    return model, {'training_history' : hist.history}


def validate_keras_model(serialized_model, weights, dataset_iterator,
    data_count):
    logger.info('Keras validation just started.')
    assert weights != None, "weights must not be 'None'."
    model = model_from_serialized(serialized_model)
    model.set_weights(weights)
    history = model.evaluate_generator(dataset_iterator, steps=data_count)
    metrics = dict(zip(model.metrics_names, history))
    logger.info('Keras validation complete.')
    return {'val_metric': metrics}


def serialize_weights(weights):
    """
    Returns a list of bytestrings of np arrays.

    `weights` is a list of np arrays (the output of model.get_weights()).
    """
    return [serialize_single_weights(w) for w in weights]

def serialize_single_weights(weight):
    memfile = io.BytesIO()
    np.save(memfile, weight)
    memfile.seek(0)
    serialized = json.dumps(memfile.read().decode('latin-1'))
    return serialized

def deserialize_weights(serialized_weights):
    """
    Returns a list of np arrays that a model can take in using
    model.set_weights().

    `serialized_weights` is a list of bytestrings of np arrays.
    """
    return [deserialize_single_weights(w) for w in serialized_weights]


def deserialize_single_weights(single_serialized_weights):
    memfile = io.BytesIO()
    memfile.write(json.loads(single_serialized_weights).encode('latin-1'))
    memfile.seek(0)
    deserialized = np.load(memfile)
    return deserialized
