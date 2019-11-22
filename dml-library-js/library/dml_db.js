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
     * @param {Tensor2D} data The data as a `Tensor2D`. 
     */
    create(dataManager, data) {        
        var timestamp = new Date().getTime();

        var db = this.db;
        this.db.get(dataManager.repoID, function(err, doc) {
            if (err) {
                var myObj = {
                    _id: dataManager.repoID,
                    data: data,
                    rows: data.length,
                    cols: data[0].length,
                    timestamp: timestamp,
                    sessions: {}
                }
                db.put(myObj, function(err, response) {
                    if (err) { return console.log(err); }
                    dataManager.connect();
                  });
            } else {
                doc.data = data;
                doc.rows = doc.data.length;
                doc.cols = doc.data[0].length;
                doc.timestamp = timestamp;
                doc.sessions = {};
                db.put(doc);
                dataManager.connect();
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
    get(runner, trainRequest) {
        var db = this.db;
        this.db.get(trainRequest.repoID, function(err, doc) {
            if (err) { return console.log(err); }
            var data = tfjs.tensor(doc.data).as2D(doc.rows, doc.cols);
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
            runner.receivedData(data, trainRequest);
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
     * @param {tf.Tensor2D} newData The data as a `Tensor2D`.
     * @param {function} callback The callback function after data is added.
     */
    addData(repoID, newData, callback=null) {
        var db = this.db
        this.db.get(repoID, function(err, doc) {
            if (err) { return console.log(err); }
            console.log("Updating data");
            doc.data = doc.data.append(newData);
            db.put(doc);
            if (callback != null) {
                callback()
            }
        });
    }
}
exports.DMLDB = DMLDB;
