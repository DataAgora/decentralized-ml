"use strict";
exports.__esModule = true;
var assert = require('assert')

/**
 * Container class for holding relevant information received from
 * the server and the repo ID.
 */
class DMLRequest {
    /**
     * Deserialize message from server.
     * 
     * @param {dict} message JSON message received from server. Must
     * have key `action` of either TRAIN or STOP.
     * 
     * @returns {DMLRequest} DML Request object.
     */
    static deserialize(repoID, message) {
        assert("action" in message, "No action found in message!")
        var action = message["action"];
        var request;
        switch (action) {
            case ("TRAIN"):
                request = new TrainRequest(repoID, message);
                break;
            case ("STOP"):
                request = new StopRequest();
                break;
            default:
                throw new Error("Received message without action!")
        }

        return request;
    }
}

class TrainRequest extends DMLRequest {
    /**
     * A type of `DMLRequest` used for facilitating training. 
     * 
     * @param {string} repoID The library's repo ID, passed in from the
     * Data Manager. 
     * @param {dict} message The message received from the server. Must 
     * have the following keys: `session_id`, `round` and `hyperparams`.
     * `hyperparams` must have keys `label_index` and `batch_size`.
     */
    constructor(repoID, message) {
        var requiredKeys = ["session_id", "round", "hyperparams"]
        requiredKeys.forEach(key => {
            assert (key in message, "TrainRequest must have ${key}!");
        })

        super();

        /** Associated repo ID for this dataset. */
        this.repoID = repoID;

        /** Session ID for the current training session. */
        this.sessionID = message["session_id"];
        
        /** Current round. */
        this.round = message["round"];

        /** Hyperparams for training. */
        this.hyperparams = message["hyperparams"]

        /** Model to train with, to be retrieved later. */
        this.model = null;
    }

    /**
     * Serialize this `TrainRequest` object for transmission to the server.
     * 
     * @param {dict} results The results from training.
     * 
     * @returns {string} Serialized `TrainRequest` string.
     */
    serialize(results) {
        var socketMessage = {
            "session_id": this.sessionID,
            "action": "TRAIN",
            "results": results,
            "round": this.round,
            "type": "NEW_UPDATE",
        };
        return JSON.stringify(socketMessage);
    }
}

/**
 * A type of `DMLRequest` just to inform the library to stop listening
 * for messages from the server.
 */
class StopRequest extends DMLRequest {
    /**
     * Serialize this `StopRequest` object for transmission to server.
     * 
     * @returns {string} Serialized `StopRequest` object.
     */
    serialize() {
        var socketMessage = {
            "success": true,
            "action": "STOP",
        }
        return JSON.stringify(socketMessage)
    }
}
exports.DMLRequest = DMLRequest;
