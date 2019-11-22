var DMLDB = require('./dml_db.js').DMLDB
var Runner = require('./runner.js').Runner;
var DataManager = require('./data_manager.js').DataManager;


var dmlDB = DMLDB();
var runner = Runner();
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
 * @param {Tensor2D} data The data as a `Tensor2D`. Refer to the TFJS API for more:
 * https://js.tensorflow.org/api/latest/#tensor2d.
 */
function bootstrapLibrary(repoID, data) {
    dataManager.bootstrap(repoID, data);
}

/**
 * Add more data after bootstrapping.
 * 
 * @param {string} repo_id The repo ID associated with the dataset.
 * @param {Tensor2D} data The data as a `Tensor2D`. Refer to the TFJS API for more:
 * https://js.tensorflow.org/api/latest/#tensor2d. 
 */
function addMoreData(repoID, data) {
    dataManager.addData(repoID, data)
}

exports.bootstrap = dataManager.bootstrap;
exports.store = dataManager.store;
exports.is_bootstrapped = dataManager.bootstrapped;
