var DMLDB = require('./dml_db.js').DMLDB
var Runner = require('./runner.js').Runner;
var DataManager = require('./data_manager.js').DataManager;


var dmlDB = new DMLDB();
var runner = new Runner(dmlDB);
var dataManager = new DataManager(dmlDB, runner);
runner.configure(dataManager)

/**
 * Returns `true` if the library is bootstrapped, `false` otherwise.
 */
function isBootstrapped() {
    return dataManager.bootstrapped
}

/**
 * Bootstrap the library by storing the initial data and connecting to the
 * server.
 * 
 * @param {string} repoID The repo ID associated with the dataset.
 * @param {tf.Tensor2D} X The datapoints to train on.
 * @param {tf.Tensor1D} y The labels for the datapoints.
 */
function bootstrapLibrary(repoID, data) {
    dataManager.bootstrap(repoID, data);
}

/**
 * Add more data after bootstrapping.
 * 
 * @param {string} repoID The repo ID associated with the dataset.
 * @param {tf.Tensor2D} X The datapoints to train on.
 * @param {tf.Tensor1D} y The labels for the datapoints.
 */
function addMoreData(repoID, data) {
    dataManager.addData(repoID, data)
}

exports.bootstrapLibrary = bootstrapLibrary;
exports.addMoreData = addMoreData;
exports.isBootstrapped = isBootstrapped;
