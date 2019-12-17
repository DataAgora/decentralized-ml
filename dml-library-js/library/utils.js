"use strict";
exports.__esModule = true;

var BASE_URL = '.au4c4pd2ch.us-west-1.elasticbeanstalk.com';

/**
 * Make the HTTP URL for the server.
 * 
 * @param {string} repoID The repo ID associated with the dataset. 
 */
function makeHTTPURL(repoID) {
    return "http://" + repoID + BASE_URL;
}

/**
 * Make the WebSocket URL for the server.
 * 
 * @param {string} repoID The repo ID associated with the dataset. 
 */
function makeWSURL(repoID) {
    return "ws://" + repoID + BASE_URL;
}

exports.makeHTTPURL = makeHTTPURL;
exports.makeWSURL = makeWSURL;