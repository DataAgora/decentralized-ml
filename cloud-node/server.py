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
from flask import Flask, jsonify, send_from_directory
from autobahn.twisted.resource import WebSocketResource, WSGIRootResource

from protocol import CloudNodeProtocol
from factory import CloudNodeFactory
from message import LibraryType
import state


app = Flask(__name__)
app.secret_key = str(uuid.uuid4())
CORS(app)

@app.route("/status")
def get_status():
    """
    Returns the status of the Cloud Node.

    The dashboard-api is the only hitting this endpoint, so it should be
    secured.
    """
    print("STARTO")
    s3_file = "Dockerfile"
    s3 = boto3.resource("s3")
    object = s3.Object("cloud-node-deployment", s3_file)
    result = object.get()['Body'].read().decode('utf-8') 
    print(result)
    return jsonify({"Busy": state.state["busy"]})

@app.route('/model/<path:filename>')
def serve_tfjs_model(filename):
    """
    Serves the TFJS model to the user.

    TODO: Should do this through ngnix for a boost in performance. Should also
    have some auth token -> session id mapping (security fix in the future).

    Args:
        filename (str): The filename to serve.
    """
    if not state.state["busy"]:
        return "No active session!\n"

    if state.state["library_type"] != LibraryType.JS.value:
        return "Current session is not for JAVASCRIPT!"

    return send_from_directory(
        os.path.join(app.root_path, state.state['tfjs_model_path']),
        filename,
    )

@app.route('/secret/reset_state')
def reset_state():
    """
    Resets the state of the cloud node.

    TODO: This is only for debugging. Should be deleted.
    """
    state.state_lock.acquire()
    state.reset_state()
    state.state_lock.release()
    return "State reset successfully!\n"

@app.route('/secret/get_state')
def get_state():
    """
    Get the state of the cloud node.

    TODO: This is only for debugging. Should be deleted.
    """
    return repr(state.state)

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

    reactor.listenTCP(8999, site)
    reactor.run()
