import json

from autobahn.twisted.websocket import WebSocketServerProtocol
from twisted.internet import reactor

import state
from message import ActionType, ErrorType, make_error_results
from new_message import validate_new_message, process_new_message


class CloudNodeProtocol(WebSocketServerProtocol):
    """
    Class that implements part of the Cloud Node networking logic (what happens
    when a new node connects, sends a message, disconnects). The networking 
    here happens through Websockets using the autobahn library.
    """

    def doPing(self):
        if self.run:
            self.sendPing()
            #print("Ping sent to {}".format(self.peer))
            reactor.callLater(10, self.doPing)

    def onPong(self, payload):
        #print("Pong received from {}".format(self.peer))
        pass

    def onConnect(self, request):
        """
        Logs that a node has successfully connected.
        """
        print("Client connecting: {}".format(request.peer))

    def onOpen(self):
        """
        Logs that a connection was opened.
        """
        self.run = True
        self.doPing()
        print("WebSocket connection open.")

    def onClose(self, wasClean, code, reason):
        """
        Deregisters a node upon websocket closure and logs it.
        """
        self.run = False
        print("WebSocket connection closed: {}".format(reason))
        success, messages = self.factory.unregister(self)
        for results in messages:
            self._broadcastMessage(
                payload=results["message"],
                client_list=results["client_list"],
                isBinary=False,
            )

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

        try:
            received_message = validate_new_message(payload)
        except Exception as e:
            if isinstance(e, json.decoder.JSONDecodeError):
                error_message = "Error while converting JSON."
            else:
                error_message = "Error deserializing message: {}"
                error_message = error_message.format(e)
            message = {
                "error": True,
                "error_message": error_message,
                "type": ErrorType.DESERIALIZATION.value
            }
            self.sendMessage(json.dumps(message).encode(), isBinary)
            print(error_message)
            return

        # Process message
        try:
            state.start_state(received_message.repo_id)
            results = process_new_message(received_message, self.factory, self)
            state.stop_state()
        except Exception as e:
            state.stop_state()
            error_message = "Error processing new message: " + str(e)
            print(error_message)
            raise e
            results = make_error_results(error_message, ErrorType.OTHER)
        
        print(results)

        if results["action"] == ActionType.BROADCAST:
            self._broadcastMessage(
                payload=results["message"],
                client_list=results["client_list"],
                isBinary=isBinary,
            )
        elif results["action"] == ActionType.UNICAST:
            message = json.dumps(results["message"]).encode()
            self.sendMessage(message, isBinary)

    def _broadcastMessage(self, payload, client_list, isBinary):
        """
        Broadcast message (`payload`) to a `client_list`.
        """
        for c in client_list:
            results_json = json.dumps(payload)
            c.sendMessage(results_json.encode(), isBinary)