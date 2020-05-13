from autobahn.twisted.websocket import WebSocketServerFactory

import state


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
        self.clients = {}

    def _new_repo(self, repo_id):
        """
        Create a new entry with the given repo ID.

        Args:
            repo_id (str): The repo ID whose clients are to be tracked.
        """
        self.clients[repo_id] = {"DASHBOARD": [], "LIBRARY": []}

    def register(self, client, client_type, repo_id):
        """
        Register `client` with the given `client_type`. Only one `DASHBOARD`
        client allowed per training session. No duplicate clients.

        Args:
            client (CloudNodeProtocol): Client to be registered.
            client_type (str): Type of client. Must be `DASHBOARD` or 
                `LIBRARY`.
        
        Returns:
            str: Error message, if an error occurred.
        """
        assert client_type in ('DASHBOARD', 'LIBRARY'), \
            "Type must be DASHBOARD or LIBRARY!"

        if repo_id not in self.clients:
            self._new_repo(repo_id)

        client_already_exists = False
        for _, clients in self.clients[repo_id].items():
            if client in clients:
                return "Client already exists!"

        if client_type == "DASHBOARD" \
                and len(self.clients[repo_id][client_type]) == 1:
            return "Only one DASHBOARD client allowed at a time!"
        
        self.clients[repo_id][client_type].append(client)
        return ""

    def unregister(self, client):
        """
        Unregister `client` if it exists.

        Args:
            client (CloudNodeProtocol): Client to be unregistered.
        
        Returns:
            bool: Returns whether unregistration was successful.
        """
        success = False
        for repo_id, repo_clients in self.clients.items():
            for node_type, clients in repo_clients.items():
                if client in clients:
                    print("Unregistered client {}".format(client.peer))
                    self.clients[repo_id][node_type].remove(client)
                    success = True
                    if node_type == "DASHBOARD":
                        state.start_state(repo_id)
                        state.num_sessions -= 1
                        state.reset_state(repo_id)
                        state.stop_state()
        
        return success

    def is_registered(self, client, client_type, repo_id):
        """
        Check whether the `client` with the given `client_type` is registered.

        Args:
            client (CloudNodeProtocol): Client to be checked.
            client_type (str): Type of client. Must be `DASHBOARD` or 
                `LIBRARY`.
            repo_id (str): The corresponding repo ID of the client.

        Returns:
            bool: Returns whether client is in the list of clients.
        """
        return repo_id in self.clients \
            and client in self.clients[repo_id][client_type]
