import os
import uuid
import json
import base64
from functools import reduce
import shutil

import boto3
import keras
import numpy as np
import tensorflowjs as tfjs
import tensorflow as tf
tf.compat.v1.disable_eager_execution()
from keras import backend as K

import state
from message import LibraryType


TEMP_FOLDER = 'temp'

def convert_and_save_b64model(base64_h5_model):
    """
    Takes the initial h5 model encoded in Base64, decodes it, saves it on
    disk (in `<TEMP_FOLDER>/<session_id>/model.h5`), then calls the helper
    function `_convert_and_save_model()` to convert the model into a tf.js
    model which will be served to library nodes.

    This function is to be called at the beginning of a DML Session with
    Javascript libraries.

    Args:
        base64_h5_model (str): base64 string of an h5 Keras model
    """
    h5_model_path = save_h5_model(base64_h5_model)
    # Convert and save model for serving
    _convert_and_save_model(h5_model_path)

def fetch_keras_model():
    """
    Download the initial Keras model.

    This function is to be called at the beginning of a DML Session.
    """
    session_id = state.state["session_id"]
    model_path = os.path.join(TEMP_FOLDER, session_id)

    # Create directory if necessary
    if not os.path.exists(model_path):
        os.makedirs(model_path)

    # Save model on disk
    h5_model_path = model_path + '/model.h5'
    try:
        repo_id = state.state["repo_id"]
        session_id = state.state["session_id"]
        round = 0
        s3 = boto3.resource("s3")
        model_s3_key = "{0}/{1}/{2}/model.h5"
        model_s3_key = model_s3_key.format(repo_id, session_id, round)
        object = s3.Object("updatestore", model_s3_key)
        object.download_file(h5_model_path)
    except Exception as e:
        print("S3 Error: {0}".format(e))

    state.state['h5_model_path'] = h5_model_path
    
    return h5_model_path
    

def get_encoded_h5_model():
    """
    Get the encoded string of the h5 Keras model.

    Returns:
        str: Returns a base64 string of the h5 Keras model
    """
    with open(state.state["h5_model_path"], mode='rb') as file:
        file_content = file.read()
        encoded_content = base64.encodebytes(file_content)
        h5_model = encoded_content.decode('ascii')
        return h5_model

def get_keras_model():
    """
    Load the Keras model from the `.h5` file.

    Returns:
        keras.engine.Model: Returns the loaded Keras model.
    """
    return keras.models.load_model(state.state["h5_model_path"])


def convert_keras_model():
    """
    Retrieves the current Keras model, converts it (from the path) into a
    tf.js model, extracts metadata from the model, and prepares the temp 
    folder where this new converted model will be served from.

    The new converted model gets stored in:
        `<TEMP_FOLDER>/<session_id>/<current_round>`

    Where the following files get created:
        - `group1.-shard1of1.bin`
        - `model.json`
        - `metadata.json`
    """
    session_id = state.state["session_id"]
    round = state.state["current_round"]
    state.state["tfjs_model_path"] = os.path.join(TEMP_FOLDER, session_id, str(round))

    _keras_2_tfjs()

    model_json_path = state.state["tfjs_model_path"] + "/model.json"
    with open(model_json_path, 'r') as fp:
        model_json = json.loads(fp.read())
        state.state["weights_shape"] = model_json["weightsManifest"][0]["weights"]

    metadata_path = state.state["tfjs_model_path"] + '/metadata.json'
    metadata = {
        "session_id": session_id,
        "current_round": round,
    }
    with open(metadata_path, 'w') as fp:
        json.dump(metadata, fp, sort_keys=True, indent=4)

def swap_weights():
    """
    Loads the initial stored h5 model in <TEMP_FOLDER>/<session_id>/model.h5,
    swaps the weights with the aggregated weights currently in the global state,
    then saves the new model in <TEMP_FOLDER>/<session_id>/model<round>.h5.

    For Javascript libraries, this function also reconverts the Keras model
    to a TFJS model.
    """
    model = get_keras_model()
    _clear_checkpoint()

    base_model_path = os.path.join(TEMP_FOLDER, state.state["session_id"])
    round = state.state["current_round"]
    new_h5_model_path = base_model_path + '/model{0}.h5'.format(round)

    if state.state["library_type"] == LibraryType.PYTHON.value:
        gradients = state.state["current_gradients"]
        learning_rate = model.optimizer.lr
        weights = model.get_weights()
        new_weights = np.subtract(weights, gradients)
        model.set_weights(new_weights)
        model.save(new_h5_model_path)
    else:
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
        model.save(new_h5_model_path)
        convert_keras_model()

    state.state['h5_model_path'] = new_h5_model_path

    K.clear_session()

def _clear_checkpoint():
    """
    Removes the current model.

    NOTE: Only call when model no longer needed!
    """
    os.remove(state.state["h5_model_path"])
    if state.state["library_type"] == LibraryType.JS.value:
        shutil.rmtree(state.state['tfjs_model_path'])

def _keras_2_tfjs():
    """
    Converts a Keras h5 model into a tf.js model and saves it on disk.
    """
    model = get_keras_model()
    tfjs.converters.save_keras_model(model, state.state["tfjs_model_path"], np.uint16)
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
