from autobahn.twisted.websocket import WebSocketServerFactory


class CloudNodeFactory(WebSocketServerFactory):
    """
    Class that implements part of the Cloud Node networking logic. It keeps
    track of the nodes that have been registered.
    """
    def __init__(self):
        """
        Set up state for clients.
        """
        WebSocketServerFactory.__init__(self)
        self.clients = {"DASHBOARD": [], "LIBRARY": []}

    def register(self, client, client_type):
        """
        Register `client` with the given `client_type`. Only one `DASHBOARD`
        client allowed per training session. No duplicate clients.

        Args:
            client (CloudNodeProtocol): Client to be registered.
            client_type (str): Type of client. Must be `DASHBOARD` or 
                `LIBRARY`.
        
        Returns:
            bool: Returns whether registration was successful.
        """
        assert client_type in ('DASHBOARD', 'LIBRARY'), \
            "Type must be DASHBOARD or LIBRARY!"
        client_already_exists = False
        for _, clients in self.clients.items():
            if client in clients:
                client_already_exists = True

        if client_type == "DASHBOARD" and len(self.clients[client_type]) == 1:
            return False, "Only one DASHBOARD client allowed at a time!"

        if client_already_exists:
            return False, "Client already exists!"
        
        self.clients[client_type].append(client)
        return True, ""

    def unregister(self, client):
        """
        Unregister `client` if it exists.

        Args:
            client (CloudNodeProtocol): Client to be unregistered.
        
        Returns:
            bool: Returns whether unregistration was successful.
        """
        success = False
        for node_type, clients in self.clients.items():
            if client in clients:
                print("Unregistered client {}".format(client.peer))
                self.clients[node_type].remove(client)
                success = True
        
        return success

    def is_registered(self, client, client_type):
        """
        Check whether the `client` with the given `client_type` is registered.

        Args:
            client (CloudNodeProtocol): Client to be checked.
            client_type (str): Type of client. Must be `DASHBOARD` or 
                `LIBRARY`.

        Returns:
            bool: Returns whether client is in the list of clients.
        """
        return client in self.clients[client_type]
