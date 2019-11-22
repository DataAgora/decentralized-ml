"use strict";
exports.__esModule = true;
var tfjs = require("@tensorflow/tfjs-node");
var PouchDB = require('pouchdb');

/**
 * @class Wrapper class around Pouch DB designed to store data using for
 * training. Keeps track of current round for sessions as well.
 * 
 * Incorporates callback behavior, as that is what PouchDB incorporates.
 */
class DMLDB {
    /** Initialize instance of PouchDB */
    constructor() {
        this.db = new PouchDB('DMLDB');
    }

    /**
     * Create a new entry in PouchDB for this dataset. 
     * 
     * An entry keeps track of the associated repoID, the data and its 
     * dimensions, the timestamp of creation and associated training
     * sessions.
     * 
     * @param {DataManager} dataManager An instance of the Data Manager.
     * Upon successful storage of the data, the DataManager connects to
     * the server.
     * @param {tf.Tensor2D} X The datapoints to train on.
     * @param {tf.Tensor1D} y The labels for the datapoints.
     */
    createDataEntry(dataManager, X, y) {        
        var timestamp = new Date().getTime();

        var db = this.db;
        this.db.get(dataManager.repoID, function(err, doc) {
            if (err) {
                var myObj = {
                    _id: dataManager.repoID,
                    X: X,
                    y: y,
                    rows: X.length,
                    cols: X[0].length,
                    timestamp: timestamp,
                    sessions: {}
                }
                db.put(myObj, function(err, response) {
                    if (err) { return console.log(err); }
                    dataManager.finishedNewStore();
                  });
            } else {
                doc.X = X;
                doc.y = y;
                doc.rows = doc.X.length;
                doc.cols = doc.X[0].length;
                doc.timestamp = timestamp;
                doc.sessions = {};
                db.put(doc);
                dataManager.finishedNewStore();
            }
          });
    }

    /**
     * Retrieve the data.
     * 
     * @param {Runner} runner An instance of the Runner. Upon successful
     * retrieval of the data, the runner begins training. 
     * @param {TrainRequest} trainRequest The request for training. 
     */
    getData(runner, trainRequest) {
        var db = this.db;
        this.db.get(trainRequest.repoID, function(err, doc) {
            if (err) { return console.log(err); }
            const X = tfjs.tensor(doc.X).as2D(doc.rows, doc.cols);
            const y = tfjs.tensor(doc.y).as1D()
            if (trainRequest.action == 'TRAIN') {
                if (!(trainRequest.id in doc.sessions)) {
                    doc.sessions[trainRequest.id] = 0;
                    db.put(doc);
                }
                var session_round = doc.sessions[trainRequest.id];
                if (session_round+ 1 != trainRequest.round) {
                    console.log("Ignoring server's message...");
                    console.log("Request's round was " + trainRequest.round + " and current round is " + session_round);
                    return;
                }
            }
            runner.receivedData(X, y, trainRequest);
        });
    }

    /**
     * Update current entry to reflect the number of rounds completed in this
     * session.
     * 
     * @param {TrainRequest} trainRequest The request to train with.
     */
    updateSession(trainRequest) {
        this.db.get(trainRequest.repoID, function(err, doc) {
            if (err) { return console.log(err); }
            doc.sessions[trainRequest.id] = trainRequest.round
            this.put(doc);
        });
    }

    /**
     * Add more data to the current entry.
     * 
     * @param {string} repoID The repo ID associated with the dataset.
     * @param {tf.Tensor2D} X The new datapoints to train on.
     * @param {tf.Tensor1D} y The labels for the new datapoints.
     * @param {function} callback The callback function after data is added.
     */
    addData(repoID, X, y, callback=null) {
        var db = this.db
        this.db.get(repoID, function(err, doc) {
            if (err) { return console.log(err); }
            console.log("Updating data");
            doc.X = doc.X.append(X);
            doc.y = doc.y.append(y);
            db.put(doc);
            if (callback != null) {
                callback()
            }
        });
    }
}
exports.DMLDB = DMLDB;
