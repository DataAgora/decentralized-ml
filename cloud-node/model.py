import os
import uuid
import json
import base64
from functools import reduce

import keras
import numpy as np
import tensorflowjs as tfjs
from keras import backend as K

import state


TEMP_FOLDER = 'temp'

def convert_and_save_b64model(base64_h5_model):
    """
    This function is to be called at the beginning of a DML Serssion.

    It takes the initial h5 model encoded in Base64, decodes it, saves it on
    disk (in <TEMP_FOLDER>/<session_id>/model.h5), then calls the helper
    function `_convert_and_save_model()` to convert the model into a tf.js
    model which will be served to library nodes.

    base64_h5_model: base64 string of an h5 keras model
    """
    session_id = state.state["session_id"]
    model_path = os.path.join(TEMP_FOLDER, session_id)

    # Create directory if necessary
    if not os.path.exists(model_path):
        os.makedirs(model_path)

    # Save model on disk
    h5_model_path = model_path + '/model.h5'
    h5_model_bytes = base64.b64decode(base64_h5_model)
    with open(h5_model_path, 'wb') as fp:
        fp.write(h5_model_bytes)

    # Convert and save model for serving
    return _convert_and_save_model(h5_model_path)


def convert_and_save_model(round):
    """
    This function is to be called when moving to a new round.

    It takes the current round number to construct the path where the model is
    stored, then it calls the helper function `_convert_and_save_model()` to
    convert the model into a tf.js model which will be served to library nodes.
    """
    session_id = state.state["session_id"]
    round = state.state["current_round"]
    model_path = os.path.join(TEMP_FOLDER, session_id)
    h5_model_path = model_path + '/model{}.h5'.format(round)
    return _convert_and_save_model(h5_model_path)


def _convert_and_save_model(h5_model_path):
    """
    Helper function that converts the given h5 model (from the path) into a
    tf.js model, extracts metadata from the model, and prepares the temp folder
    where this new converted model will be served from.

    The new converted model gets stored in:
        <TEMP_FOLDER>/<session_id>/<current_round>

    Where the following files get created:
        - group1.-shard1of1.bin
        - model.json
        - metadata.json

    This function returns the path to the converted model on disk.
    """
    session_id = state.state["session_id"]
    round = state.state["current_round"]
    converted_model_path = os.path.join(TEMP_FOLDER, session_id, str(round))

    _keras_2_tfjs(h5_model_path, converted_model_path)

    model_json_path = converted_model_path + "/model.json"
    with open(model_json_path, 'r') as fp:
        model_json = json.loads(fp.read())
        state.state["weights_shape"] = model_json["weightsManifest"][0]["weights"]

    metadata_path = converted_model_path + '/metadata.json'
    metadata = {
        "session_id": session_id,
        "current_round": round,
    }
    with open(metadata_path, 'w') as fp:
        json.dump(metadata, fp, sort_keys=True, indent=4)

    return converted_model_path


def swap_weights():
    """
    Loads the initial stored h5 model in <TEMP_FOLDER>/<session_id>/model.h5,
    swaps the weights with the aggregated weights currently in the global state,
    then saves the new model in <TEMP_FOLDER>/<session_id>/model<round>.h5.

    This function is to be called before running `convert_and_save_model()`
    when moving to a new round.
    """
    model_path = os.path.join(TEMP_FOLDER, state.state["session_id"])
    h5_model_path = model_path + '/model.h5'
    model = keras.models.load_model(h5_model_path)

    weights_flat = state.state["current_weights"]
    weights_shape = state.state["weights_shape"]
    weights, start = [], 0
    for shape_data in weights_shape:
        shape = shape_data["shape"]
        size = reduce(lambda x, y: x*y, shape)
        weights_np = np.array(weights_flat[start:start+size])
        weights_np.resize(tuple(shape))
        weights.append(weights_np)
        start += size
    model.set_weights(weights)

    round = state.state["current_round"]
    new_h5_model_path = model_path + '/model{0}.h5'.format(round)
    model.save(new_h5_model_path)
    K.clear_session()

def _keras_2_tfjs(h5_model_path, path_to_save):
    """
    Converts a Keras h5 model into a tf.js model and saves it on disk.
    """
    model = keras.models.load_model(h5_model_path)
    tfjs.converters.save_keras_model(model, path_to_save, np.uint16)
    K.clear_session()

def _test():
    """
    Nothing important here.
    """
    state.init()
    out = _convert_and_save_model('../notebooks/saved_mlp_model_with_w.h5')
    print(out)


# def decode_weights(h5_model_path):
#     """
#     Do Keras stuff here
#     """
#     model = keras.models.load_model(h5_model_path)
#     weights = model.get_weights()
#     return weights


# def _test2():
#     out = decode_weights('../notebooks/saved_mlp_model_with_w.h5')
#     print(out)
