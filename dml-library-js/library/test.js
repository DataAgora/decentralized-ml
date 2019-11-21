"use strict";

var DMLDB = require('./dml_db.js').DMLDB
var dml_db = new DMLDB();
var DataManager = require('./data_manager.js').DataManager
var data_manager = new DataManager(dml_db)
var tf = require("@tensorflow/tfjs-node");
const repo_id = "99885f00eefcd4107572eb62a5cb429a";
console.log(data_manager)

async function run() {
  const data = await getData();
  console.log("Data retrieved!");
  data_manager.bootstrap(repo_id, data);  
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
