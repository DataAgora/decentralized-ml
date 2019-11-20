from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import logging
import random
import os

import numpy as np
import tensorflow as tf

from server import Server
from client import TensorflowClient, KerasClient

logging.basicConfig(level=logging.ERROR,
                    format='%(asctime)s %(levelname)s %(message)s')
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
logging.getLogger('tensorflow').disabled = True

# Set random seeds for reproducibility.
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)
tf.set_random_seed(RANDOM_SEED)

class Experiment:
    def __init__(self, config):
        logging.info('Starting experiment.')
        self.config = config
        self.num_clients = config['num_clients']
        self.model_type = config['model_type']
        self.dataset_type = config['dataset_type']
        self.fraction = config['fraction']
        self.max_rounds = config['max_rounds']

        # Set up datasets
        logging.info('Setting up datasets.')
        X_train_list, y_train_list, X_test, y_test = \
            self.get_datasets(self.num_clients, self.model_type, self.dataset_type)

        # Make the clients and server and connect them
        logging.info('Setting up server and clients.')
        if self.model_type == 'lstm':
            Client = KerasClient
        else:
            Client = TensorflowClient
        self.clients = []
        i = 1
        for X, y in zip(X_train_list, y_train_list):
            self.clients.append(Client(i, X, y))
            i += 1
        self.validation_client = Client('val', X_test, y_test)
        self.server = Server(self.clients, self.validation_client, config)

        # Set up models
        logging.info('Setting up the deep models.')
        self.batch_size = config['batch_size']
        self.epochs = config['epochs']
        self.learning_rate = config['learning_rate']
        for client in self.clients:
            client.setup_model(self.model_type)
        self.validation_client.setup_model(self.model_type)
        logging.info('Done setting up experiment.')

    def get_datasets(self, num_clients, model_type, dataset_type):
        # Load training and eval data
        if model_type == 'perceptron' or model_type == 'cnn-mnist':
            mnist = tf.contrib.learn.datasets.load_dataset("mnist")
            X_train = np.concatenate((mnist.train.images, mnist.validation.images))
            y_train = np.concatenate((
                        np.asarray(mnist.train.labels, dtype=np.int32),
                        np.asarray(mnist.validation.labels, dtype=np.int32),
                      ))
            X_test = mnist.test.images
            y_test = np.asarray(mnist.test.labels, dtype=np.int32)

            if model_type == 'perceptron':
                X_train = X_train.reshape(-1, 784)
                X_test = X_test.reshape(-1, 784)
            if model_type == 'cnn-mnist':
                X_train = X_train.reshape(-1, 28, 28, 1)
                X_test = X_test.reshape(-1, 28, 28, 1)
        elif model_type == 'cnn-cifar10':
            # NOTE: the paper doesn't implement cifar-mnist and non-iid.
            cifar_data = tf.keras.datasets.cifar10.load_data()
            training_data, testing_data = cifar_data
            X_train, y_train = training_data
            X_test, y_test = testing_data
        else:
            raise ValueError('Model type {0} not supported.'.format(model_type))

        # Partition data
        if dataset_type == 'iid':
            # Shuffle data (train and test)
            indices = np.random.permutation(X_train.shape[0])
            X_train, y_train = X_train[indices], y_train[indices]
            indices = np.random.permutation(X_test.shape[0])
            X_test, y_test = X_test[indices], y_test[indices]

            # Partition data
            X_train_list = np.split(X_train, num_clients)
            y_train_list = np.split(y_train, num_clients)
        else:
            raise ValueError('Dataset type {0} not supported.'.format(dataset_type))

        return X_train_list, y_train_list, X_test, y_test

    def run(self):
        self.server.federated_learning(self.fraction, self.max_rounds, self.model_type)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--notes', type=str, help="notes about the \
        experiment (default <none>)", default="")
    parser.add_argument('-k', '--clients', type=int, help="number of clients \
        to instantiate (default 1)", default=1)
    parser.add_argument('-m', '--model', type=str, help="type of deep model \
        (specifies the dataset) (default perceptron)", default="perceptron")
    parser.add_argument('-d', '--datasettype', type=str, help="type of dataset \
        partition (default IID)", default="iid")
    parser.add_argument('-c', '--fraction', type=float, help="fraction of \
        clients to train on (default 1.0)", default=1.0)
    parser.add_argument('-r', '--maxrounds', type=int, help="maximum number \
        of communication rounds (default 100000)", default=100000)
    parser.add_argument('-b', '--batchsize', type=int, help="local batchsize \
        (default 50)", default=50)
    parser.add_argument('-e', '--epochs', type=int, help="number of local \
        epochs (-1 implies the whole dataset) (default 5)", default=5)
    parser.add_argument('-l', '--learningrate', type=float, help="learning rate \
        (default 1e-4)", default=1e-4)
    parser.add_argument('-f', '--savedir', type=str, help="directory to save \
        validation history (default './results')", default='./results')
    parser.add_argument('-g', '--goalaccuracy', type=float, help="accuracy \
        when training should stop (default 1.0)", default=1.0)
    parser.add_argument('-y', '--decay', type=float, help="learning rate decay \
        (default 0.99)", default=0.99)
    parser.add_argument('-a', '--avgtype', type=str, help="type of averaging \
        algorithm (data_size, val_acc) (default data_size)", default="data_size")
    args = parser.parse_args()

    config = {
        "notes": args.notes,
        "num_clients": args.clients,
        "model_type": args.model,
        "dataset_type": args.datasettype,
        "fraction": args.fraction,
        "max_rounds": args.maxrounds,
        "batch_size": args.batchsize,
        "epochs": args.epochs,
        "learning_rate": args.learningrate,
        "save_dir": args.savedir,
        "goal_accuracy": args.goalaccuracy,
        "lr_decay": args.decay,
        "averaging_type": args.avgtype
    }

    experiment = Experiment(config)
    experiment.run()
