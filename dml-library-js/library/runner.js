exports.__esModule = true;

var tf = require("@tensorflow/tfjs-node");
var fetch = require('node-fetch');

var DMLRequest = require("./message.js").DMLRequest;
var DMLDB = require("./dml_db.js").DMLDB;
var makeHTTPURL = require('utils').makeHTTPURL

/**
 * Utility class for training TFJS models.
 * 
 * NOTE: Only `tf.LayersModel` models are supported at this time.
 */
class Runner {

    /**
     * Configure the Runner with an instance of the Data Manager.
     * 
     * @param {DataManager} dataManager An instance of the Data Manager.
     * Upon completion of training, the Data Manager sends the training
     * results back to the server.
     */
    configure(dataManager) {
        this.dataManager = dataManager
    }

    /**
     * Handle a received message from the Data Manager
     * 
     * @param {TrainRequest} request The request for training.
     */
    async handleRequest(trainRequest) {
        await this._prepareTraining(trainRequest); 
    }

    /**
     * Get the model, compile it and retrieve the data.
     * 
     * @param {TrainRequest} trainRequest The request for training. 
     */
    async _prepareTraining(trainRequest) {
        const model_url = makeHTTPURL(trainRequest.repoID) + "/model/model.json";
        var model = await tf.loadLayersModel(model_url);
        var runner = this;
        fetch(model_url)
        .then(res => res.json())
        .then((out) => {
            model = runner._compileModel(model, out["modelTopology"]["training_config"]);
            trainRequest.model = model
            DMLDB.get(this, trainRequest);
        }).catch(err => console.error(err));
    }

    /**
     * Compile a TFJS `LayersModel`.
     * 
     * @param {tf.LayersModel} model LayersModel to be compiled.
     * @param {dict} optimization_data Optimization data from the model.json
     * 
     * @returns {tf.LayersModel} The compiled LayersModel.
     */
    _compileModel(model, optimization_data) {
        var optimizer;
        var optimizerConfig = optimization_data['optimizer_config']
        if (optimizerConfig['class_name'] == 'SGD') {
            optimizer = tf.train.sgd(optimizerConfig['config']['learning_rate']);
        } else if (optimizerConfig['class_name'] == 'Adam') {
            optimizer = tf.train.adam(optimizerConfig['config']['learning_rate'], optimizerConfig['config']['beta1'], optimizerConfig['config']['beta2'])
        } else {
            // Not supported!
            throw new Error("Optimizer not supported!");
        }
        model.compile({
            optimizer: optimizer,
            loss: this._lowerCaseToCamelCase(optimization_data['loss']),
            metrics: optimization_data['metrics']
        });
        return model;
    }

    /**
     * Helper function to convert string from snake_case to camelCase
     * 
     * @param {string} str String in snake_case
     * 
     * @returns {string} String in camelCase 
     */
    _snakeCaseToCamelCase (str) {
        return str.replace(/_([a-z])/g, function (g) { return g[1].toUpperCase(); });
    };

    /**
     * Callback function for the DMLDB when the data is retrieved.
     * 
     * @param {Tensor2D} data The data as a `Tensor2D`.
     * @param {TrainRequest} trainRequest The request for training. 
     */
    receivedData(data, trainRequest) {
        this._train(data, trainRequest);
    }

    /**
     * Train the model with the given data.
     * 
     * @param {Tensor2D} data The data as a `Tensor2D`.
     * @param {TrainRequest} trainRequest The request for training. 
     */
    async _train(data, trainRequest) {
        console.log("Starting round: " + trainRequest.round)
        var [dataX, dataY] = this._labelData(data.arraySync(), trainRequest.params.label_index);
        trainRequest.model.fit(dataX, dataY, {
            batchSize: trainRequest.params["batch_size"],
            epochs: trainRequest.params["epochs"],
            shuffle: trainRequest.params["shuffle"],
            verbose: 0
        });
        console.log("Finished training!");
        var weights = await this._getWeights(trainRequest.model)
        var results = {
            "weights": weights,
            "omega": data.arraySync().length
        }
        this.dataManager.finishedTraining(trainRequest, results) 
    }

    /**
     * Assign the labels in the dataset.
     * 
     * @param {Tensor2D} data The data as a `Tensor2D`.
     * @param {int} label_index The index of the column that has the labels.
     * 
     * @returns {list} List of 2 lists. The first list is the
     * datapoints without the labels, and the second list is the labels.
     */
    _labelData(data, label_index) {
        if (label_index < 0) {
            label_index = data[0].length - 1;
        }
        var trainXs = data;
        var trainYs = trainXs.map(function (row) { return row[label_index]; });
        trainXs.forEach(function (x) { x.splice(label_index, 1); });
        return [tf.tensor(trainXs), tf.tensor(trainYs)];
    };

    /**
     * Extract the weights from the model.
     * 
     * @param {tf.LayersModel} model The model after training.
     * 
     * @returns {list} List of weights.
     */
    async _getWeights(model) {
        var all_weights = [];
        for (var i = 0; i < model.layers.length * 2; i++) {
        // Time 2 so we can get the bias too.
        let weights = model.getWeights()[i];
        let weightsData = weights.dataSync();
        let weightsList = Array.from(weightsData);
        for (var j = 0; j < weightsList.length; j++) {
            all_weights.push(weightsList[j]);
        }
        }
        return all_weights;
    };





    static async _sendMessage(trainRequest, message) {
        
    }


}

exports.Runner = Runner;
