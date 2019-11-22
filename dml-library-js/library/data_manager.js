"use strict";
exports.__esModule = true;
var DMLRequest = require("./message.js").DMLRequest;
var makeWSURL = require('./utils.js').makeWSURL;
const WebSocket = require('ws');


class DataManager {
    /** 
     * Brain of the library. Prepares local data for training, manages
     * communication, and passes train requests to the Runner. 
     * 
     * @param {DMLDB} db An instance of DMLDB for storing data.
     * @param {Runner} runner An instance of the Runner for training.
     * */
    constructor(db, runner) {
        this.dmlDB = db;
        this.runner = runner;
        /** WebSocket used to communicate with server for incoming messages */
        this.ws = null;
        /** Repo ID associated with dataset */
        this.repoID = null;
        /** `true` if library has been bootstrapped, `false` otherwise */
        this.bootstrapped = false;
    }

    /**
     * Bootstrap the library by storing the initial data and connecting to the
     * server.
     * 
     * @param {string} repoID The repo ID associated with the dataset.
     * @param {Tensor2D} data The data as a `Tensor2D`. Refer to the TFJS API for more:
     * https://js.tensorflow.org/api/latest/#tensor2d.
     */
    bootstrap(repoID, data) {
        if (this.bootstrapped) {
            return;
        }
        this.repoID = repoID;
        this.dmlDB.create(this, data.arraySync());
    }

    /**
     * Add more data after bootstrapping.
     * 
     * @param {string} repoID The repo ID associated with the dataset.
     * @param {Tensor2D} data The data as a `Tensor2D`. Refer to the TFJS API for more:
     * https://js.tensorflow.org/api/latest/#tensor2d.
     */
    addData(repoID, data) {
        if (!this.bootstrapped)
            throw new Error("Library not bootstrapped!");
        this.dmlDB.addData(repoID, data.arraySync(), null);
    }

    /**
     * Callback function for a finished new store by the DMLDB.
     */
    finishedNewStore() {
        this._connect()
    }

    /**
     * Connect to the server.
     */
    _connect() {
        var dataManager = this;
        dataManager.ws = new WebSocket(makeWSURL(dataManager.repoID));
        dataManager.ws.addEventListener("open", function (event) {
            console.log("Connection successful!");
            dataManager.bootstrapped = true;
            var registrationMessage = {
                "type": "REGISTER",
                "node_type": "LIBRARY"
            };
            this.send(JSON.stringify(registrationMessage));
            dataManager._listen();
        });

        dataManager.ws.addEventListener("error", function (event) {
            throw new Error("Bootstrap failed due to a failure to connect. Please check the repo id to make sure it is valid!");
        });

    }

    /**
     * Listen for TRAIN or STOP messages from the server.
     */
    _listen() {
        this.ws.addEventListener('message', function (event) {
            var receivedMessage = event.data;
            var message = JSON.parse(receivedMessage)
            if ("action" in message) {
                if (message["action"] == "TRAIN") {
                    console.log("\nReceived new TRAIN message!")
                    var request = DMLRequest._deserialize(message);
                    request.ws = this;
                    this.runner._handleMessage(request);
                } else if (message["action"] == "STOP") {
                    console.log("Received STOP message. Stopping...")
                } else {
                    console.log("Received unknown action. Stopping...")
                }
            } else {
                console.log("No action in message. Stopping...")
            }
        });

        var dataManager = this;
        this.ws.addEventListener("close", function (event) {
            console.log("Connection lost. Reconnecting...")
            //console.log(event);
            if (event.code == 1006) {
                dataManager._connect();
            }
        });
        this.bootstrapped = true;
        console.log("Bootstrapped!");
    }

    /**
     * Callback function for the Runner after training is done.
     * 
     * @param {trainRequest} trainRequest The request for training.
     * @param {string} results The results from training. 
     */
    finishedTraining(trainRequest, results) {
        var message = DMLRequest._serialize(trainRequest, results);
        this.ws.send(message);
        this.dmlDB.updateSession(trainRequest, Runner._sendMessage, results);
    }
}
exports.DataManager = DataManager;
