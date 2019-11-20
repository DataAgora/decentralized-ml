import json
import base64

from autobahn.twisted.websocket import WebSocketClientProtocol

# This ID is used to log things into DynamoDB.
# If you want your results to be saved somewhere you can easily access, then
# change this to something you can remember.
REPO_ID = "mnist"

CLOUD_NODE_HOST = "99885f00eefcd4107572eb62a5cb429a.au4c4pd2ch.us-west-1.elasticbeanstalk.com"
CLOUD_NODE_PORT = 80

with open('assets/init_mlp_model_with_w.h5', mode='rb') as file:
    file_content = file.read()
    encoded_content = base64.b64encode(file_content)
    h5_model = encoded_content.decode('ascii')

NEW_MESSAGE = {
    "type": "NEW_SESSION",
    "repo_id": REPO_ID,
    "h5_model": h5_model,
    "hyperparams": {
        "batch_size": 8000,
        "epochs": 5,
        "shuffle": True, 
        "label_index": 0
    },
    "selection_criteria": {
        "type": "ALL_NODES",
    },
    "continuation_criteria": {
        "type": "PERCENTAGE_AVERAGED",
        "value": 0.75
    },
    "termination_criteria": {
        "type": "MAX_ROUND",
        "value": 1
    }
}

NEW_CONNECTION_MESSAGE = {
    "type": "REGISTER",
    "node_type": "dashboard",
}

class NewSessionTestProtocol(WebSocketClientProtocol):

   def onOpen(self):
      json_data = json.dumps(NEW_CONNECTION_MESSAGE)
      self.sendMessage(json_data.encode())
      json_data = json.dumps(NEW_MESSAGE)
      self.sendMessage(json_data.encode())

   def onMessage(self, payload, isBinary):
      if isBinary:
         print("Binary message received: {0} bytes".format(len(payload)))
      else:
         print("Text message received: {0}".format(payload.decode('utf8')))

if __name__ == '__main__':

   import sys

   from twisted.python import log
   from twisted.internet import reactor
   log.startLogging(sys.stdout)

   from autobahn.twisted.websocket import WebSocketClientFactory
   factory = WebSocketClientFactory()
   factory.protocol = NewSessionTestProtocol

   reactor.connectTCP(CLOUD_NODE_HOST, CLOUD_NODE_PORT, factory)
   reactor.run()