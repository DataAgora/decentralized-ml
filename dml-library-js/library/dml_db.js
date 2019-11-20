"use strict";
exports.__esModule = true;
var tfjs_1 = require("@tensorflow/tfjs-node");
var PouchDB = require('pouchdb');

class DMLDB {
    static _open() {
        DMLDB.db = new PouchDB('DMLDB');
    }

    static _create(repo, data, callback) {        
        var timestamp = new Date().getTime();

        DMLDB.db.get(repo, function(err, doc) {
            if (err) {
                var myObj = {
                    _id: repo,
                    data: data,
                    rows: data.length,
                    cols: data[0].length,
                    timestamp: timestamp,
                    sessions: {}
                }
                DMLDB.db.put(myObj, function(err, response) {
                    if (err) { return console.log(err); }
                    callback();
                  });
            } else {
                doc.data = data;
                doc.rows = doc.data.length;
                doc.cols = doc.data[0].length;
                doc.timestamp = timestamp;
                doc.sessions = {};
                DMLDB.db.put(doc);
                callback();
            }
            
            // handle doc
          });
    }

    static _get(dml_request, callback, model) {
        DMLDB.db.get(dml_request.repo, function(err, doc) {
            if (err) { return console.log(err); }
            var data = tfjs_1.tensor(doc.data).as2D(doc.rows, doc.cols);
            if (dml_request.action == 'TRAIN') {
                if (!(dml_request.id in doc.sessions)) {
                    doc.sessions[dml_request.id] = 0;
                    DMLDB.db.put(doc);
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

    static _put(dml_request, callback, result) {
        DMLDB.db.get(dml_request.repo, function(err, doc) {
            if (err) { return console.log(err); }
            //console.log("Updating round on session");
            doc.sessions[dml_request.id] = dml_request.round
            //console.log(doc.sessions)
            DMLDB.db.put(doc);
            callback(dml_request, result);
        });
    }

    static update_data(repo, new_data, callback) {
        DMLDB.db.get(repo, function(err, doc) {
            if (err) { return console.log(err); }
            console.log("Updating data");
            doc.data = doc.data.append(new_data);
            DMLDB.db.put(doc);
            if (callback != null) {
                callback()
            }
        });
    }
}
exports.DMLDB = DMLDB;
