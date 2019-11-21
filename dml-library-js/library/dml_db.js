"use strict";
exports.__esModule = true;
var tfjs_1 = require("@tensorflow/tfjs-node");
var PouchDB = require('pouchdb');

class DMLDB {
    constructor() {
        this.db = new PouchDB('DMLDB');
    }

    create(data_manager, data) {        
        var timestamp = new Date().getTime();
        const repo_id = data_manager.repo_id;

        var db = this.db;
        this.db.get(repo_id, function(err, doc) {
            if (err) {
                var myObj = {
                    _id: repo_id,
                    data: data,
                    rows: data.length,
                    cols: data[0].length,
                    timestamp: timestamp,
                    sessions: {}
                }
                db.put(myObj, function(err, response) {
                    if (err) { return console.log(err); }
                    data_manager.connect();
                  });
            } else {
                doc.data = data;
                doc.rows = doc.data.length;
                doc.cols = doc.data[0].length;
                doc.timestamp = timestamp;
                doc.sessions = {};
                db.put(doc);
                data_manager.connect();
            }
            
            // handle doc
          });
    }

    _get(dml_request, callback, model) {
        var db = this.db;
        this.db.get(dml_request.repo, function(err, doc) {
            if (err) { return console.log(err); }
            var data = tfjs_1.tensor(doc.data).as2D(doc.rows, doc.cols);
            if (dml_request.action == 'TRAIN') {
                if (!(dml_request.id in doc.sessions)) {
                    doc.sessions[dml_request.id] = 0;
                    db.put(doc);
                }
                var session_round = doc.sessions[dml_request.id];
                if (session_round+ 1 != dml_request.round) {
                    console.log("Ignoring server's message...");
                    console.log("Request's round was " + dml_request.round + " and current round is " + session_round);
                    return;
                }
            }
            callback(data, dml_request, model);
        });
    }

    _put(dml_request, callback, result) {
        this.db.get(dml_request.repo, function(err, doc) {
            if (err) { return console.log(err); }
            //console.log("Updating round on session");
            doc.sessions[dml_request.id] = dml_request.round
            //console.log(doc.sessions)
            this.put(doc);
            callback(dml_request, result);
        });
    }

    update_data(repo, new_data, callback) {
        this.get(repo, function(err, doc) {
            if (err) { return console.log(err); }
            console.log("Updating data");
            doc.data = doc.data.append(new_data);
            this.put(doc);
            if (callback != null) {
                callback()
            }
        });
    }
}
exports.DMLDB = DMLDB;
