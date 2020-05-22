import sys
import uuid
import json
import io
import os

import boto3
import tensorflow as tf
from flask_cors import CORS, cross_origin
from twisted.python import log
import werkzeug.formparser
from twisted.web.server import Site
from twisted.web.wsgi import WSGIResource
from twisted.internet import task, reactor
from flask import Flask, jsonify, send_from_directory, send_file
from autobahn.twisted.resource import WebSocketResource, WSGIRootResource

from protocol import CloudNodeProtocol
from factory import CloudNodeFactory
from message import LibraryType
import state


app = Flask(__name__)
app.secret_key = str(uuid.uuid4())
CORS(app)

@app.route("/status/<repo_id>", methods=["GET"])
def get_status(repo_id):
    """
    Returns the status of the Cloud Node.

    The dashboard-api is the only hitting this endpoint, so it should be
    secured.
    """
    state.start_state(repo_id)
    try:
        status = jsonify({"Busy": state.state["busy"]})
    except Exception as e:
        print("Exception getting status: " + str(e))
        state.stop_state()
        return
    state.stop_state()
    return status

@app.route('/model/<session_id>/<path:filename>', methods=["GET"])
def serve_tfjs_model(session_id, filename):
    """
    Serves the TFJS model to the user.

    TODO: Should do this through ngnix for a boost in performance. Should also
    have some auth token -> session id mapping (security fix in the future).

    Args:
        filename (str): The filename to serve.
    """
    if not state.start_state_by_session_id(session_id):
        return "No active session!\n"
    try:
        if not state.state["busy"]:
            return "No active session!\n"
        if state.state["library_type"] != LibraryType.JS.value:
            return "Current session is not for JAVASCRIPT!"
        folder_path = os.path.join(app.root_path, state.state['tfjs_model_path'])
    except Exception as e:
        print("Exception getting TFJS model: " + str(e))
        state.stop_state()
        return
    state.stop_state()
    return send_from_directory(folder_path, filename)

@app.route('/mlmodel/<session_id>', methods=["GET"])
def serve_mlmodel(session_id):
    """
    Serves the mlmodel model to the user.

    TODO: Should do this through ngnix for a boost in performance. Should also
    have some auth token -> session id mapping (security fix in the future).
    """
    if not state.start_state_by_session_id(session_id):
        return "No active session!\n"
    try:
        if not state.state["busy"]:
            return "No active session!\n"
        if state.state["library_type"] != LibraryType.IOS_IMAGE.value:
            return "Current session is not for IOS!"
        app_path = os.path.join(app.root_path, state.state['mlmodel_path'])
    except Exception as e:
        print("Exception getting mlmodel: " + str(e))
        state.stop_state()
        return
    state.stop_state()
    return send_file(app_path)

@app.route('/mlmodel/weights/<session_id>', methods=["GET"])
def serve_mlmodel_weights(session_id):
    """
    Serves the TFJS model to the user.

    TODO: Should do this through ngnix for a boost in performance. Should also
    have some auth token -> session id mapping (security fix in the future).
    """
    if not state.start_state_by_session_id(session_id):
        return "No active session!\n"
    try:
        if not state.state["busy"]:
            return "No active session!\n"
        if state.state["library_type"] != LibraryType.IOS_TEXT.value:
            return "Current session is not for IOS!"
        app_path = os.path.join(app.root_path, state.state['mlmodel_weights_path'])
    except Exception as e:
        print("Exception getting mlmodel weights: " + str(e))
        state.stop_state()
        return

    state.stop_state()
    return send_file(app_path)

@app.route('/keras/<session_id>', methods=['POST', 'GET'])
def serve_keras_model(session_id):
    if not state.start_state_by_session_id(session_id):
        return "No active session!\n"
    try:
        if not state.state["busy"]:
            return "No active session!\n"
        if state.state["library_type"] != LibraryType.PYTHON.value:
            return "Current session is not for PYTHON!"
        app_path = os.path.join(app.root_path, state.state['h5_model_path'])
    except Exception as e:
        print("Exception getting Keras model: " + str(e))
        state.stop_state()
        return
    
    state.stop_state()
    return send_file(app_path)

@app.route('/reset_state/<repo_id>', methods=["GET"])
def reset_state(repo_id):
    """
    Resets the state of the cloud node.
    """
    state.start_state(repo_id)
    try:
        state.reset_state(repo_id)
    except Exception as e:
        print("Exception resetting state: " + str(e))
        state.stop_state()
        return
    state.stop_state()
    return "State reset successfully!"

@app.route('/get_state/<repo_id>')
def get_state(repo_id):
    """
    Get the state of the cloud node.
    """
    state.start_state(repo_id)
    try:
        state_dict = repr(state.state)
    except Exception as e:
        print("Exception getting state: " + str(e))
        state.stop_state()
        return
    
    state.stop_state()
    return state_dict

if __name__ == '__main__':
    tf.compat.v1.disable_eager_execution()
    log.startLogging(sys.stdout)

    factory = CloudNodeFactory()
    factory.protocol = CloudNodeProtocol
    wsResource = WebSocketResource(factory)

    wsgiResource = WSGIResource(reactor, reactor.getThreadPool(), app)
    rootResource = WSGIRootResource(wsgiResource, {b'': wsResource})
    site = Site(rootResource)

    state.init()

    reactor.listenTCP(80, site)
    reactor.run()
