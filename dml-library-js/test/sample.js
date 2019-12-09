console.log("Importing discreet-dml.")
// Importing the DML package
var discreetai = require('discreet-dml');
console.log("importing tfjs and mnist")
// Importing other needed packages
var tf = require("@tensorflow/tfjs-node");
var mnist = require('mnist');


// Repo ID after creating a repo. See https://beta.discreetai.com
repo_id = "28f4bfc658e7ae91b0372414d68df9b4"

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

// Store the data with a given repo name, and wait for incoming messages to train on the data.
// discreet.store(repo_id, getData());
discreetai.bootstrap(repo_id, getData())

