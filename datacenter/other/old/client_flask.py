import logging
import pickle
import uuid
import socket

import numpy as np
import tensorflow as tf
from flask import Flask, request


from models.perceptron import Perceptron

logging.basicConfig(level=logging.DEBUG,
                    format='[Client ] %(asctime)s %(levelname)s %(message)s')
app = Flask(__name__)

class Client(object):
    def __init__(self, iden):
        self.iden = iden

    def setup_data(self, X_train, y_train):
        self.X_train = X_train
        self.y_train = y_train

    def setup_model(self, model_type):
        self.model_type = model_type
        if model_type == "perceptron":
            self.model = Perceptron()
        else:
            raise ValueError("Model {model_type} not supported." \
                .format(model_type))

    def setup_training(self, batch_size, epochs, learning_rate):
        self.batch_size = self.X_train.shape[0] if batch_size == -1 else batch_size
        self.epochs = epochs
        self.params = {'learning_rate': learning_rate}

    def train(self, weights):
        logging.info('Training just started.')
        if weights:
            metagraph = self.create_fresh_metagraph(fresh_weights=(weights == None))
            self.model.load_weights(weights, metagraph, self.get_checkpoints_folder())
            tf.reset_default_graph()
            logging.info('Fresh metagraph created.')

        classifier = tf.estimator.Estimator(
            model_fn=self.model.get_model,
            model_dir=self.get_checkpoints_folder(),
            params = self.params
        )
        # tensors_to_log = {"probabilities": "softmax_tensor"}
        # logging_hook = tf.train.LoggingTensorHook(
        #     tensors=tensors_to_log, every_n_iter=50)
        train_input_fn = tf.estimator.inputs.numpy_input_fn(
            x={"x": self.X_train},
            y=self.y_train,
            batch_size=self.batch_size,
            num_epochs=self.epochs,
            shuffle=True
        )
        classifier.train(
            input_fn=train_input_fn,
            #hooks=[logging_hook]
        )
        logging.info('Training complete.')

        weights = self.model.get_weights(self.get_latest_checkpoint())

        metagraph_dir = self.get_latest_checkpoint() + '.meta'
        with open(metagraph_dir, 'rb') as f:
            metagraph_contents = f.read()
        f.close()

        return weights, metagraph_contents, self.X_train[0].size

    def create_fresh_metagraph(self, fresh_weights):
        tf.reset_default_graph()
        train_input_fn = tf.estimator.inputs.numpy_input_fn(
            x={"x": self.X_train},
            y=self.y_train,
            batch_size=1,
            num_epochs=None,
            shuffle=False
        )
        #tensors_to_log = {"probabilities": "softmax_tensor"}
        #logging_hook = tf.train.LoggingTensorHook(tensors=tensors_to_log, every_n_iter=1)
        classifier = tf.estimator.Estimator(
            model_fn=self.model.get_model,
            model_dir=self.get_checkpoints_folder(),
            params = self.params
        )
        classifier.train(input_fn=train_input_fn, steps=1)

        tf.reset_default_graph()
        with tf.Session().as_default() as sess:
            new_saver = tf.train.import_meta_graph(
                self.get_latest_checkpoint() + '.meta'
            )
            meta_graph_def = tf.train.export_meta_graph()

            if fresh_weights:
                sess.run(tf.global_variables_initializer())
                new_saver.save(sess, self.get_latest_checkpoint())
        tf.reset_default_graph()
        return meta_graph_def

    def get_checkpoints_folder(self):
        return "./checkpoints-{0}/{1}/".format(self.iden, self.model_type)

    def get_latest_checkpoint(self):
        return tf.train.latest_checkpoint(self.get_checkpoints_folder())

@app.route('start')

@app.route('/train', methods=['POST'])
def train():
    content = request.get_json()
    client.


@app.route('/setup', methods=['POST'])
def setup():
    content = request.get_json()

    client = Client()
    client.setup_data(X_train, y_train)
    client.setup_model(model_type)
    client.setup_training(batch_size, epochs, learning_rate)

def get_ephemeral_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('localhost', 0))
    port = sock.getsockname()[1]
    sock.close()
    return port

if __name__ == '__main__':
    port = get_ephemeral_port()
    app.run(port=port)
