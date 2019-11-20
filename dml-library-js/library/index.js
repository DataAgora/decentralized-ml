var DataManager = require('./data_manager.js').DataManager

exports.bootstrap = DataManager.bootstrap;
exports.store = DataManager.store;
exports.bootstrap_and_store = DataManager.bootstrap_and_store
exports.listen = DataManager._listen;
exports.is_bootstrapped = DataManager.bootstrapped;
exports.has_data = DataManager.has_data;

DataManager.initialize()

exports.printMsg = function() {
    console.log("This is a message from the demo package");
}
