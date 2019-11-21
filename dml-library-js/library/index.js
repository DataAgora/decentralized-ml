var DMLDB = require('./dml_db.js').DMLDB
var dml_db = DMLDB();
var DataManager = require('./data_manager.js').DataManager
var data_manager = new DataManager(dml_db)


/**
 * Returns `true` if the library is bootstrapped, `false` otherwise.
 */
function is_bootstrapped() {
    return data_manager.is_bootstrapped
}

/**
 * Bootstrap the library by storing the initial data and connecting to the
 * server.
 * 
 * @param {string} repo_id 
 * @param {Tensor2D} data 
 */
function bootstrap_library(repo_id, data) {
    data_manager.bootstrap(repo_id, data);
}

/**
 * Add more data after bootstrapping.
 * 
 * @param {string} repo_id 
 * @param {Tensor2D} data 
 */
function add_more_data(repo_id, data) {
    data_manager.add_data(repo_id, data)
}
exports.bootstrap = data_manager.bootstrap;
exports.store = data_manager.store;
exports.is_bootstrapped = data_manager.bootstrapped;
