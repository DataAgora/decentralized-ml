import sys
import uuid
import json

from flask_cors import CORS
from twisted.python import log

from twisted.web.server import Site
from twisted.web.wsgi import WSGIResource
from twisted.internet import task, reactor
from flask import Flask, send_from_directory
from autobahn.twisted.websocket import WebSocketServerProtocol
from autobahn.twisted.websocket import WebSocketServerFactory
from autobahn.twisted.resource import WebSocketResource, WSGIRootResource

import state
from message import MessageType, Message
from coordinator import start_new_session
from aggregator import handle_new_weights


class CloudNodeProtocol(WebSocketServerProtocol):

    def onConnect(self, request):
        print("Client connecting: {}".format(request.peer))
        print(state.state)

    def onOpen(self):
        print("WebSocket connection open.")

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {}".format(reason))
        self.factory.unregister(self)

    def onMessage(self, payload, isBinary):
        if isBinary:
            print("Binary message not supported.")
            return

        # Convert message to JSON
        try:
            serialized_message = json.loads(payload)
        except Exception:
            print("Error converting JSON.")
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
            if message.node_type in ["DASHBOARD", "LIBRARY"]:
                self.factory.register(self, message.node_type)
                print("Registered node as type: {}".format(message.node_type))

                if message.node_type == "LIBRARY" and state.state["busy"] is True:
                    # There's a session active, we should incorporate the just
                    # added node!
                    print("Joining the new library node to this round!")
                    last_message = state.state["last_message_sent_to_library"]
                    message_json = json.dumps(last_message)
                    self.sendMessage(message_json.encode(), isBinary)
            else:
                print("WARNING: Incorrect node type ({}) -- ignoring!".format(message.node_type))
        elif message.type == MessageType.NEW_SESSION.value:
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
        else:
            print("Unknown message type!")
            error_json = json.dumps({"error": True, "message": "Unknown message type!"})
            self.sendMessage(error_json.encode(), isBinary)

        print("[[DEBUG] State: {}".format(state.state))

    def _broadcastMessage(self, payload, client_list, isBinary):
        for c in client_list:
            results_json = json.dumps(payload)
            c.sendMessage(results_json.encode(), isBinary)

class CloudNodeFactory(WebSocketServerFactory):

    def __init__(self):
        WebSocketServerFactory.__init__(self)
        self.clients = {"DASHBOARD": [], "LIBRARY": []}

    def register(self, client, type):
        client_already_exists = False
        for _, clients in self.clients.items():
            if client in clients:
                client_already_exists = True
        if not client_already_exists:
            print("Registered client {}".format(client.peer))
            self.clients[type].append(client)

    def unregister(self, client):
        for node_type, clients in self.clients.items():
            if client in clients:
                print("Unregistered client {}".format(client.peer))
                self.clients[node_type].remove(client)

# // NOTE: We need to implement some ping-pong/ways to deal with disconnections.

app = Flask(__name__)
app.secret_key = str(uuid.uuid4())
CORS(app)

@app.route('/model/<path:filename>')
def serve_model(filename):
    """
    Serves the models to the user.
    TODO: Should do this through ngnix for a boost in performance. Should also
    have some auth token -> session id mapping (security fix in the future).
    """
    session_id = state.state["session_id"]
    round = state.state["current_round"]
    return send_from_directory(
        app.root_path + '/temp/' + session_id + "/" + str(round),
        filename,
    )

@app.route('/secret/reset_state')
def reset_state():
    """
    Resets the state of the cloud node.
    """
    state.state_lock.acquire()
    state.reset_state()
    state.state_lock.release()
    return "State was reset!"

@app.route('/secret/get_state')
def get_state():
    """
    Get the state of the cloud node.
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
