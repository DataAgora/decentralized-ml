var http = require('http');

http.createServer(function (req, res) {
  res.writeHead(200, {'Content-Type': 'text/html'});
  res.end('Hello World!');
}).listen(8080);

var WebSocketServer = require('ws').Server,
ws = new WebSocketServer({port: 8001});

connections = []
ws.on('connection', function(w){
    var index = connections.length - 1;
    connections.push(w)
    w.send("Hi Client!");
    console.log("Connected with client!");
    w.on('message', function(msg){
        //var id = w.upgradeReq.headers['sec-websocket-key'];
        console.log("Client sent us weights!");
    });
    var timer = setTimeout(sendMessage, 15000);
    w.on('close', function() {
        console.log("Closing client...");
        connections.splice(index, 1);
    });

    //sockets[id] = w;
});

function sendMessage() {
    console.log("Sending messages!");
    for (var i = 0; i < connections.length; i++) {
        var params = {
            "batch_size": 8000,
            "epochs": 5,
            "shuffle": true, 
            "label_index": 0
          }
        var message = {
            "session_id": "test",
            "repo": "mnist",
            "action": "TRAIN",
            "hyperparams": params,
            "current_round": 1
        }
        connections[i].send(JSON.stringify(message));
    }
}




