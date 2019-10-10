console.log("Importing dataagora-dml.")
// Importing the DML package
var dataagora = require('dataagora-dml');
console.log("importing tfjs and mnist")
// Importing other needed packages
var tf = require("@tensorflow/tfjs-node");
var mnist = require('mnist');


// Repo ID after creating a repo. See https://beta.dataagora.com
repo_id = "99885f00eefcd4107572eb62a5cb429a"

// Get data. Must be of type Tensor2D.
function getData() {
    var set = mnist.set(8000, 0);

    var trainingSet = set.training;
    var data = []

    for (var i = 0; i < trainingSet.length; i++) {
        data.push(trainingSet[i].input);
        data[i].push(trainingSet[i].output.indexOf(1));
    }
    return tf.tensor(data).as2D(8000, 785);
}

// Bootstrap the library with the repo_id.
// dataagora.bootstrap(repo_id);

// Store the data with a given repo name, and wait for incoming messages to train on the data.
// dataagora.store(repo_id, getData());
dataagora.bootstrap_and_store(repo_id, getData())

