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
     * @param {DMLDB} dmlDB An instance of DMLDB for storing data.
     * @param {Runner} runner An instance of the Runner for training.
     * */
    constructor(dmlDB, runner) {
        this.dmlDB = dmlDB;
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
     * @param {tf.Tensor2D} X The datapoints to train on.
     * @param {tf.Tensor1D} y The labels for the datapoints. 
     */
    bootstrap(repoID, X, y) {
        if (this.bootstrapped) {
            return;
        }
        this.repoID = repoID;
        this.dmlDB.createDataEntry(this, X.arraySync(), y.arraySync());
    }

    /**
     * Add more data after bootstrapping.
     * 
     * @param {string} repoID The repo ID associated with the dataset.
     * @param {tf.Tensor2D} X The datapoints to train on.
     * @param {tf.Tensor1D} y The labels for the datapoints.
     * @param {function} [callback=null] The callback function after data is added.
     */
    addData(repoID, X, y, callback=null) {
        if (!this.bootstrapped)
            throw new Error("Library not bootstrapped!");
        this.dmlDB.addData(repoID, X.arraySync(), y.arraySync());
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
        var dataManager = this;

        this.ws.addEventListener('message', function (event) {
            var receivedMessage = event.data;
            var message = JSON.parse(receivedMessage)
            if ("action" in message) {
                if (message["action"] == "TRAIN") {
                    console.log("\nReceived new TRAIN message!")
                    var request = DMLRequest.deserialize(dataManager.repoID, message);
                    request.ws = this;
                    dataManager.runner.handleRequest(request);
                } else if (message["action"] == "STOP") {
                    console.log("Received STOP message. Stopping...")
                } else {
                    console.log("Received unknown action. Stopping...")
                }
            } else {
                console.log("No action in message. Stopping...")
            }
        });

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
        var message = trainRequest.serialize(results);
        this.ws.send(message);
        this.dmlDB.updateSession(trainRequest);
    }
}
exports.DataManager = DataManager;
