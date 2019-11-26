import json

from autobahn.twisted.websocket import WebSocketServerProtocol

import state
from message import MessageType, Message, LibraryType
from coordinator import start_new_session, add_model_to_new_message
from aggregator import handle_new_weights


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