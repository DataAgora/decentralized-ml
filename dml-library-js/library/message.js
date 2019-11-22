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
     * @returns {DMLRequest} Returns a DML Request object.
     */
    static deserialize(repo_id, message) {
        assert("action" in message, "No action found in message!")
        var action = message["action"];
        var request;
        switch (action) {
            case ("TRAIN"):
                request = new TrainRequest(repo_id, message);
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
     * @param {string} repo_id The library's repo ID, passed in from the
     * Data Manager. 
     * @param {dict} message The message received from the server. Must 
     * have the following keys: `session_id`, `round` and `hyperparams`.
     */
    constructor(repo_id, message) {
        assert("session_id" in message, "TrainRequest must have repo_id!");
        assert("round" in message, "TrainRequest must have round!");
        assert("hyperparams" in message, "TrainRequest must have hyperparams!");

        /** Associated repo ID for this dataset. */
        this.repo_id = repo_id;

        /** Session ID for the current training session. */
        this.session_id = message["session_id"];
        
        /** Current round. */
        this.round = message["round"];

        /** Hyperparams for training. */
        this.hyperparams = message["hyperparams"]
    }

    /**
     * Serialize this `TrainRequest` object for transmission to the server.
     * 
     * @returns {string} Serialized `TrainRequest` string.
     */
    serialize() {
        var socketMessage = {
            "session_id": this.session_id,
            "action": "TRAIN",
            "results": message,
            "round": this.round,
            "type": "NEW_WEIGHTS",
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
