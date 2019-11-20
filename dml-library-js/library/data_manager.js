"use strict";
exports.__esModule = true;
var DMLDB = require("./dml_db.js").DMLDB;
var DMLRequest = require("./message.js").DMLRequest;
var Runner = require("./runner.js").Runner;
const WebSocket = require('ws');

class DataManager {
    static initialize() {
        DataManager.bootstrapped = false;
        DataManager.has_data = false;
        DataManager.base_url = ".au4c4pd2ch.us-west-1.elasticbeanstalk.com"
    }

    static _connect(repo_id, data, callback) {
        console.log("Connecting to: " + DataManager.cloud_url);
        DataManager.ws = new WebSocket(DataManager.ws_url);
        DataManager.ws.addEventListener("open", function (event) {
            console.log("Connection successful!");
            DataManager.bootstrapped = true;
            var registrationMessage = {
                "type": "REGISTER",
                "node_type": "LIBRARY"
            };
            DataManager.ws.send(JSON.stringify(registrationMessage));
            if (data == null) {
                callback();
            } else {
                callback(repo_id, data);
            }
                
        });

        DataManager.ws.addEventListener("error", function (event) {
            throw new Error("Bootstrap failed due to a failure to connect. Please check the repo id to make sure it is valid!");
        });

    }

    static bootstrap(repo_id, data, callback) {
        if (DataManager.bootstrapped) {
            DataManager._listen();
        } else {
            DMLDB._open();
            DataManager._connect(repo_id, data, callback);
            console.log("Bootstrapped!");
        }
    }

    static store(repo, data) {
        if (!DataManager.bootstrapped)
            throw new Error("Library not bootstrapped!");
        if (DataManager.has_data) {
            DMLDB.update_store(repo, data, null);
        } else {
            DMLDB._create(repo, data.arraySync(), DataManager._listen);
            DataManager.has_data = true;
        }
        console.log("Data stored!");
    }

    static bootstrap_and_store(repo_id, data, test) {
        if (test) {
            DataManager.repo_id = repo_id;
            DataManager.cloud_url = "http://localhost:8999";
            DataManager.ws_url = "ws://localhost:8999";
        } else {
            DataManager.repo_id = repo_id;
            DataManager.cloud_url = "http://" + repo_id + DataManager.base_url;
            DataManager.ws_url = "ws://" + repo_id + DataManager.base_url
        }
        DataManager.bootstrap(repo_id, data, DataManager.store);
    }

    static _listen() {
        DataManager.ws.addEventListener('message', function (event) {
            var receivedMessage = event.data;
            //console.log("Received message:");
            //console.log(receivedMessage);
            var request_json = JSON.parse(receivedMessage)
            if ("action" in request_json) {
                if (request_json["action"] == "TRAIN") {
                    console.log("\nReceived new TRAIN message!")
                    var request = DMLRequest._deserialize(request_json);
                    request.cloud_url = DataManager.cloud_url
                    request.ws = DataManager.ws;
                    Runner._handleMessage(request);
                } else if (request_json["action"] == "STOP") {
                    console.log("Received STOP message. Stopping...")
                } else {
                    console.log("Received unknown action. Stopping...")
                }
            } else {
                console.log("No action in message. Stopping...")
            }
        });

        DataManager.ws.addEventListener("close", function (event) {
            console.log("Connection lost. Reconnecting...")
            //console.log(event);
            if (event.code == 1006) {
                DataManager._connect(DataManager.repo_id, null, DataManager._listen);
            }
        });
    }
}
exports.DataManager = DataManager;
