import uuid
import os
import json
import io

import numpy as np
import keras
import keras.backend as K

from custom.keras import model_from_serialized
from core.utils.filesys import ensure_dir
import logging 

logger = logging.getLogger('Utils/Keras')
# import logging as utils_logging

# utils_logging.basicConfig(level=utils_logging.INFO,
#                     format='[Utils/Keras] %(asctime)s %(levelname)s %(message)s')

def train_keras_model(model, dataset_iterator, data_count,
    hyperparams, config, gradients=False):
    logger.info('Keras training just started.')
    if gradients:
        accumulated_gradients = None
        total_loss = 0
        batch = 1
        for X, y in dataset_iterator:
            learning_rate = model.optimizer.lr
            loss, accuracy = model.train_on_batch(X, y)
            print("Finished training on batch {0} with loss {1} and accuracy {2}")
            gradients = calculate_gradients(model, X, y)
            if accumulated_gradients is None:
                accumulated_gradients = np.zeros(gradients.shape)
            accumulated_gradients = np.add(accumulated_gradients, np.multiply(gradients, learning_rate))
            batch += 1
        accumulated_gradients = [K.eval(gradient).tolist() for gradient in accumulated_gradients]
        return model, accumulated_gradients
    else:
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

def calculate_gradients(model, X, y):
    weights = model.trainable_weights # weight tensors
    gradients = model.optimizer.get_gradients(model.total_loss, weights) # gradient tensors

    input_tensors = [model.inputs[0], # input data
                    model.sample_weights[0], # how much to weight each sample by
                    model.targets[0], # labels
                    K.learning_phase(), # train or test mode
    ]

    get_gradients = K.function(inputs=input_tensors, outputs=gradients)

    inputs = [X, # X
            np.ones(len(X)), # sample weights
            y, # y
            0 # learning phase in TEST mode
    ]

    gradients = np.array(get_gradients(inputs))
    return gradients

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
