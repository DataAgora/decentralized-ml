"use strict";
exports.__esModule = true;
var DMLDB = require("./dml_db.js").DMLDB;
var DMLRequest = require("./message.js").DMLRequest;
var Runner = require("./runner.js").Runner;
const WebSocket = require('ws');


/** 
 * @class Brain of the library. Prepares local data for training and waits
 * for new training messages to pass on to the rest of the library. 
 * */
class DataManager {
    /**
     *  
     */
    constructor(db) {
        /** An instance of DMLDB for storing data. */
        this.dml_db = db;
        /** WebSocket used to communicate with server for incoming messages */
        this.ws = null;
        /** Repo ID associated with dataset */
        this.repo_id = null;
        /** `true` if library has been bootstrapped, `false` otherwise */
        this.bootstrapped = false;
        /** Base url of server */
        this.BASE_URL = ".au4c4pd2ch.us-west-1.elasticbeanstalk.com"
    }

    /**
     * Connect to the server.
     */
    connect() {
        const ws_url = "ws://" + this.repo_id + this.BASE_URL
        var data_manager = this;
        data_manager.ws = new WebSocket(ws_url);
        data_manager.ws.addEventListener("open", function (event) {
            console.log("Connection successful!");
            data_manager.bootstrapped = true;
            var registrationMessage = {
                "type": "REGISTER",
                "node_type": "LIBRARY"
            };
            this.send(JSON.stringify(registrationMessage));
            data_manager._listen();
        });

        data_manager.ws.addEventListener("error", function (event) {
            throw new Error("Bootstrap failed due to a failure to connect. Please check the repo id to make sure it is valid!");
        });

    }

    /**
     * Bootstrap the library by storing the initial data and connecting to the
     * server.
     * 
     * @param {string} repo_id The repo ID associated with the dataset.
     * @param {Tensor2D} data The data as a `Tensor2D`. Refer to the TFJS API for more:
     * https://js.tensorflow.org/api/latest/#tensor2d.
     */
    bootstrap(repo_id, data) {
        if (this.bootstrapped) {
            return;
        }
        this.repo_id = repo_id;
        this.dml_db.create(this, data.arraySync());
    }

    /**
     * Add more data after bootstrapping.
     * 
     * @param {string} repo_id The repo ID associated with the dataset.
     * @param {Tensor2D} data The data as a `Tensor2D`. Refer to the TFJS API for more:
     * https://js.tensorflow.org/api/latest/#tensor2d.
     */
    add_data(repo_id, data) {
        if (!this.bootstrapped)
            throw new Error("Library not bootstrapped!");
        this.dml_db.update_store(repo, data.arraySync(), null);
    }

    /**
     * Listen for TRAIN or STOP messages from the server.
     */
    _listen() {
        const cloud_url = "ws://" + this.repo_id + this.BASE_URL;
        this.ws.addEventListener('message', function (event) {
            var receivedMessage = event.data;
            var request_json = JSON.parse(receivedMessage)
            if ("action" in request_json) {
                if (request_json["action"] == "TRAIN") {
                    console.log("\nReceived new TRAIN message!")
                    var request = DMLRequest._deserialize(request_json);
                    request.cloud_url = cloud_url
                    request.ws = this;
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

        var data_manager = this;
        this.ws.addEventListener("close", function (event) {
            console.log("Connection lost. Reconnecting...")
            //console.log(event);
            if (event.code == 1006) {
                data_manager._connect();
            }
        });
        this.bootstrapped = true;
        console.log("Bootstrapped!");
    }
}
exports.DataManager = DataManager;
