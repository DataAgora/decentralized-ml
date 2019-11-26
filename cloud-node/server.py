from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys
import uuid
import json

import io

from flask_cors import CORS, cross_origin
from twisted.python import log

import werkzeug.formparser

from twisted.web.server import Site
from twisted.web.wsgi import WSGIResource
from twisted.internet import task, reactor
from flask import Flask, jsonify, send_from_directory
from autobahn.twisted.websocket import WebSocketServerProtocol
from autobahn.twisted.websocket import WebSocketServerFactory
from autobahn.twisted.resource import WebSocketResource, WSGIRootResource

import state
from message import MessageType, Message, LibraryType
from coordinator import start_new_session, add_model_to_new_message
from aggregator import handle_new_weights
import os

import keras

import tensorflowjs as tfjs


from tensorflow.keras import backend as K
import tensorflow as tf

tf.compat.v1.disable_eager_execution()

print(tf.__version__)

class CloudNodeProtocol(WebSocketServerProtocol):
    """
    Cloud Node Protocol

    Class that implements part of the Cloud Node networking logic (what happens
    when a new node connects, sends a message, disconnects). The networking here
    happens through Websockets using the autobahn library.

    """

    def onConnect(self, request):
        """
        Logs that a node has successfully connected.
        """
        print("Client connecting: {}".format(request.peer))

    def onOpen(self):
        """
        Logs that a connection was opened.
        """
        print("WebSocket connection open.")

    def onClose(self, wasClean, code, reason):
        """
        Deregisters a node upon websocket closure and logs it.
        """
        print("WebSocket connection closed: {}".format(reason))
        self.factory.unregister(self)

    def onMessage(self, payload, isBinary):
        """
        Processes the payload received by a connected node.

        Messages are ignored unless the message is of type "REGISTER" or the
        node has already been registered (by sending a "REGISTER" type message).

        """
        print("Got payload!")
        if os.path.isfile("creds.py"):
            import creds
        if isBinary:
            print("Binary message not supported.")
            return

        # Convert message to JSON
        try:
            serialized_message = json.loads(payload)
        except Exception:
            print("Error while converting JSON.")
            return

        # Deserialize message
        try:
            message = Message.make(serialized_message)
            print("Message ({0}) contents: {1}".format(message.type, message))
        except Exception as e:
            print("Error deserializing message!", e)
            error_json = json.dumps({"error": True, "message": "Error deserializing message: {}".format(e)})
            self.sendMessage(error_json.encode(), isBinary)
            return

        # Process message
        if message.type == MessageType.REGISTER.value:
            # Register the node
            if message.node_type in ["DASHBOARD", "LIBRARY"]:
                self.factory.register(self, message.node_type)
                print("Registered node as type: {}".format(message.node_type))

                if message.node_type == "LIBRARY" and state.state["busy"] is True:
                    # There's a session active, we should incorporate the just
                    # added node into the session!
                    print("Adding the new library node to this round!")
                    last_message = state.state["last_message_sent_to_library"]
                    if state.state["library_type"] == LibraryType.PYTHON.value:
                        last_message = add_model_to_new_message(last_message)
                    message_json = json.dumps(last_message)
                    self.sendMessage(message_json.encode(), isBinary)
                    # print("Session active. Registering, but not adding to this round.")
            else:
                print("WARNING: Incorrect node type ({}) -- ignoring!".format(message.node_type))
        elif message.type == MessageType.NEW_SESSION.value:
            # Verify this node has been registered
            if not self._nodeHasBeenRegistered(client_type="DASHBOARD"): return
            # Start new DML Session
            results = start_new_session(message, self.factory.clients)

            # Error check
            if results["error"]:
                self.sendMessage(json.dumps(results).encode(), isBinary)
                return

            # Handle results
            if results["action"] == "BROADCAST":
                self._broadcastMessage(
                    payload=results["message"],
                    client_list=results["client_list"],
                    isBinary=isBinary,
                )

        elif message.type == MessageType.NEW_WEIGHTS.value:
            # Verify this node has been registered
            if not self._nodeHasBeenRegistered(client_type="LIBRARY"): return

            if not self.factory.clients["DASHBOARD"]: 
                state.state.reset()
                print("Disconnected from dashboard client, stopping session.")
                return

            # Handle new weights (average, move to next round, terminate session)
    
            results = handle_new_weights(message, self.factory.clients)

            # Error check
            if results["error"]:
                self.sendMessage(json.dumps(results).encode(), isBinary)
                return

            # Handle message
            if "action" in results:
                if results["action"] == "BROADCAST":
                    self._broadcastMessage(
                        payload=results["message"],
                        client_list=results["client_list"],
                        isBinary=isBinary,
                    )
            else:
                # Acknowledge message (temporarily! -- node doesn't need to know)
                self.sendMessage(json.dumps({"error": False, "message": "ack"}).encode(), isBinary)
                message = {
                    "session_id": state.state["session_id"],
                    "repo_id": state.state["repo_id"],
                    "action": "NEW_MODEL"
                }
                self._broadcastMessage(
                    payload=message,
                    client_list = self.factory.clients["DASHBOARD"],
                    isBinary=isBinary
                )
        else:
            print("Unknown message type!")
            error_json = json.dumps({"error": True, "message": "Unknown message type!"})
            self.sendMessage(error_json.encode(), isBinary)

        print("[[DEBUG] State: {}".format(state.state))

    def _broadcastMessage(self, payload, client_list, isBinary):
        """
        Broadcast message (`payload`) to a `client_list`.
        """
        for c in client_list:
            results_json = json.dumps(payload)
            c.sendMessage(results_json.encode(), isBinary)

    def _nodeHasBeenRegistered(self, client_type):
        """
        Returns whether the node in scope has been registered into one of the
        `client_type`'s.
        """
        return self.factory.is_registered(self, client_type)

class CloudNodeFactory(WebSocketServerFactory):

    """
    Cloud Node Factory

    Class that implements part of the Cloud Node networking logic. It keeps
    track of the nodes that have been registered.

    """

    def __init__(self):
        WebSocketServerFactory.__init__(self)
        self.clients = {"DASHBOARD": [], "LIBRARY": []}

    def register(self, client, type):
        client_already_exists = False
        for _, clients in self.clients.items():
            if client in clients:
                client_already_exists = True
        if not client_already_exists:
            if type == "LIBRARY" or len(self.clients[type]) == 0:
                print("Registered client {}".format(client.peer))
                self.clients[type].append(client)
            else:
                print("Only one dashboard client allowed at a time!")

    def unregister(self, client):
        for node_type, clients in self.clients.items():
            if client in clients:
                print("Unregistered client {}".format(client.peer))
                self.clients[node_type].remove(client)

    def is_registered(self, client, client_type):
        """Returns whether client is in the list of clients."""
        return client in self.clients[client_type]

# NOTE: We need to implement some ping-pong/ways to deal with disconnections.

app = Flask(__name__)
app.secret_key = str(uuid.uuid4())
CORS(app)

@app.route("/status")
def get_status():
    """
    Returns the status of the Cloud Node.

    The dashboard-api is the only hitting this endpoint, so it should be secured.
    """
    return jsonify({"Busy": state.state["busy"]})

@app.route('/model/<path:filename>')
def serve_model(filename):
    """
    Serves the models to the user.

    TODO: Should do this through ngnix for a boost in performance. Should also
    have some auth token -> session id mapping (security fix in the future).
    """
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
    return "State reset successfully!"

@app.route('/secret/get_state')
def get_state():
    """
    Get the state of the cloud node.

    TODO: This is only for debugging. Should be deleted.
    """
    return repr(state.state)

# def check_timeout_condition():
#     """
#     TO BE IMPLEMENTED.
#     """
#     TIMEOUT_DELTA_IN_MINS = 10
#     time_now = time.time()
#     if time_now > TIMEOUT_DELTA_IN_MINS * 60:
#         # Need to trigger the event of broadcasting to all nodes.
#         # The nodes to drop everything they were doing.
#         pass


if __name__ == '__main__':

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
