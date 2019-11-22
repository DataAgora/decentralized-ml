"use strict";
var tf = require("@tensorflow/tfjs-node");

var DMLDB = require('./dml_db.js').DMLDB
var Runner = require('./runner.js').Runner;
var DataManager = require('./data_manager.js').DataManager;


var dmlDB = new DMLDB();
var runner = new Runner(dmlDB);
var dataManager = new DataManager(dmlDB, runner);
runner.configure(dataManager)

const repo_id = "99885f00eefcd4107572eb62a5cb429a";

async function run() {
  const [X, y] = await getData();
  console.log("Data retrieved!");
  dataManager.bootstrap(repo_id, X, y);  
}

async function getData(label_index=0) {
  var mnist = require('mnist'); // this line is not needed in the browser

  var set = mnist.set(8000, 0);

  var trainingSet = set.training;
  var data = []

  for (var i = 0; i < trainingSet.length; i++) {
    data.push(trainingSet[i].input);
    data[i].push(trainingSet[i].output.indexOf(1));
  }

  if (label_index < 0) {
    label_index = data[0].length - 1;
  }
  var trainXs = data;
  var trainYs = trainXs.map(function (row) { return row[label_index]; });
  trainXs.forEach(function (x) { x.splice(label_index, 1); });
  return [tf.tensor(trainXs).as2D(8000, 784), tf.tensor(trainYs).as1D()];
}
  
run()
