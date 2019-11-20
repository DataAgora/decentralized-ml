"use strict";

var DataManager = require('./data_manager.js').DataManager;
var tf = require("@tensorflow/tfjs-node");
const repo_id = "c0e533b747a0792b90d388597ea5c79b";
DataManager.initialize();
console.log(DataManager)

async function run() {
  const data = await getData();
  console.log("Data retrieved!");
  DataManager.bootstrap_and_store(repo_id, data);  
}

async function getData() {
  var mnist = require('mnist'); // this line is not needed in the browser

  var set = mnist.set(8000, 0);

  var trainingSet = set.training;
  var data = []

  for (var i = 0; i < trainingSet.length; i++) {
    data.push(trainingSet[i].input);
    data[i].push(trainingSet[i].output.indexOf(1));
  }
  return tf.tensor(data).as2D(8000, 785);
}
  
run()
