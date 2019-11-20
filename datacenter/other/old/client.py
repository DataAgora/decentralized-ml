import logging
import pickle
import shutil
import random

import numpy as np
import tensorflow as tf
import keras

from models.perceptron import Perceptron
from models.cnn import CNN
from models.lstm import LSTMModel

from models.keras_perceptron import KerasPerceptron

logging.basicConfig(level=logging.DEBUG,
                    format='[Client] %(asctime)s %(levelname)s %(message)s')

class TensorflowClient(object):
    def __init__(self, iden, X, y):
        self.iden = iden
        self.X = X
        self.y = y

        # TODO: Should be randomized.
        cut_off = int(X.shape[0] * 0.8)
        self.X_train = X[:cut_off]
        self.y_train = y[:cut_off]
        self.X_test = X[cut_off:]
        self.y_test = y[cut_off:]

    def setup_model(self, model_type):
        self.model_type = model_type
        if model_type == "perceptron":
            self.model = Perceptron()
        elif model_type == "cnn-mnist":
            self.model = CNN()
        elif model_type == "cnn-cifar10":
            self.model = CNN()
        else:
            raise ValueError("Model {0} not supported.".format(model_type))

    def train(self, weights, config):
        logging.info('Training just started.')
        assert weights != None, 'weights must not be None.'

        assert config["averaging_type"] in ["data_size", "val_acc"]
        if config["averaging_type"] == "data_size":
            X, y = self.X, self.y
        elif config["averaging_type"] == "val_acc":
            X, y = self.X_train, self.y_train

        batch_size = X.shape[0] \
            if config["batch_size"] == -1 else config["batch_size"]
        epochs = config["epochs"]
        learning_rate = config["learning_rate"]
        params = {'new_weights': weights, 'learning_rate': learning_rate}

        classifier = tf.estimator.Estimator(
            model_fn=self.model.get_model,
            model_dir=self.get_checkpoints_folder(),
            params = params
        )
        train_input_fn = tf.estimator.inputs.numpy_input_fn(
            x={"x": X},
            y=y,
            batch_size=batch_size,
            num_epochs=epochs,
            shuffle=True
        )
        classifier.train(input_fn=train_input_fn)
        logging.info('Training complete.')
        new_weights = self.model.get_weights(self.get_latest_checkpoint())

        if config["averaging_type"] == "data_size":
            omega = X.shape[0]
        elif config["averaging_type"] == "val_acc":
            eval_classifier = tf.estimator.Estimator(
                model_fn=self.model.get_model,
                model_dir=self.get_checkpoints_folder(),
                params = {'new_weights': new_weights}
            )
            eval_input_fn = tf.estimator.inputs.numpy_input_fn(
                x={"x": self.X_test},
                y=self.y_test,
                num_epochs=1,
                shuffle=False
            )
            eval_results = eval_classifier.evaluate(input_fn=eval_input_fn)
            omega = eval_results["accuracy"]

        shutil.rmtree("./checkpoints-{0}/".format(self.iden))
        return new_weights, omega

    def validate(self, t, weights, config):
        # check if this is needed
        model_type = config["model_type"]
        self.setup_model(model_type)
        classifier = tf.estimator.Estimator(
            model_fn=self.model.get_model,
            model_dir=self.get_checkpoints_folder(),
            params = {'new_weights': weights, 'learning_rate': 0.0}
        )
        train_input_fn = tf.estimator.inputs.numpy_input_fn(
            x={"x": self.X},
            y=self.y,
            batch_size=1,
            num_epochs=None,
            shuffle=False
        )
        classifier.train(
            input_fn=train_input_fn,
            steps=1
        )

        metagraph_file = self.get_checkpoints_folder() + '.meta'
        self.model.load_weights(weights, self.get_latest_checkpoint(),
            self.get_checkpoints_folder())
        logging.info('Main model updated.')

        self.setup_model(model_type)
        classifier = tf.estimator.Estimator(
            model_fn=self.model.get_model,
            model_dir=self.get_checkpoints_folder(),
            params = {'new_weights': weights}
        )
        eval_input_fn = tf.estimator.inputs.numpy_input_fn(
            x={"x": self.X},
            y=self.y,
            num_epochs=1,
            shuffle=False
        )
        eval_results = classifier.evaluate(input_fn=eval_input_fn)
        logging.info("[Round {0}] Validation results: {1}".format(t, eval_results))
        return eval_results

    def get_initial_weights(self, model_type):
        tf.reset_default_graph()
        if model_type == "perceptron":
            m = Perceptron()
            inputs = tf.placeholder(tf.float32, shape=(None, 28*28))
            _ = m.get_model(features={"x": inputs}, labels=None, mode='predict', params=None)
        elif model_type == 'cnn-mnist':
            m = CNN()
            inputs = tf.placeholder(tf.float32, shape=(None, 28, 28, 1))
            _ = m.get_model(features={"x": inputs}, labels=None, mode='predict', params=None)
        elif model_type == 'cnn-cifar10':
            m = CNN()
            inputs = tf.placeholder(tf.float32, shape=(None, 32, 32, 3))
            _ = m.get_model(features={"x": inputs}, labels=None, mode='predict', params=None)
        else:
            raise ValueError("Model {model_type} not supported.".format(model_type))
        with tf.Session().as_default() as sess:
            sess.run(tf.global_variables_initializer())
            collection = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES)
            weights = {tensor.name:sess.run(tensor) for tensor in collection}
        tf.reset_default_graph()
        return weights

    def get_checkpoints_folder(self):
        return "./checkpoints-{0}/{1}/".format(self.iden, self.model_type)

    def get_latest_checkpoint(self):
        return tf.train.latest_checkpoint(self.get_checkpoints_folder())

class KerasClient(object):
    def __init__(self, iden, X, y):
        self.iden = iden
        self.X = X
        self.y = y

    def setup_model(self, model_type):
        self.model_type = model_type
        if model_type == "lstm":
            self.model = LSTMModel()
        else:
            raise ValueError("Model {0} not supported.".format(model_type))

    def train(self, weights, config):
        logging.info('Training just started.')
        assert weights != None, 'weights must not be None.'
        self.model.set_weights(weights)
        self.model.train(X)
        logging.info('Training complete.')
        new_weights = self.model.get_weights()
        return new_weights, len(X)

    def validate(self, t, weights, config):
        # TODO: Need to implement Keras validation.
        pass

    def get_initial_weights(self):
        return self.model.get_initial_weights()
