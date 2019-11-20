import time
import random
import json
import logging
import pathlib
from math import ceil

import numpy as np
import tensorflow as tf
import ray

from models.generic_model import GenericTensorflowModel, GenericKerasModel

logging.basicConfig(level=logging.DEBUG,
                    format='[Server] %(asctime)s %(levelname)s %(message)s')

class Server:
    def __init__(self, clients, validation_client, config):
        self.clients = clients
        self.validation_client = validation_client
        self.config = config
        self.val_history = {
            "duration" : [],
            "config": config,
            "learning_rate": []
        }
        self.save_path = self.config['save_dir'] + "/" + str(time.time())

        if config['model_type'] == 'lstm':
            self.model = GenericKerasModel()
        else:
            self.model = GenericTensorflowModel()

    def get_initial_weights(self, model_type):
        """
        Asks one of the clients to send the initial weights (it asks the
        validation node for now).
        """
        return self.validation_client.get_initial_weights(model_type)


    def validate_model(self, t, weights, start_time):
        # Get validation accuracy
        eval_results = self.validation_client.validate(t, weights, self.config)
        self.best_accuracy = max(self.best_accuracy, eval_results["accuracy"])

        # Update validation history
        for key, value in eval_results.items():
            if key not in self.val_history:
                self.val_history[key] = []
            self.val_history[key].append(float(value))
        elapsed_time = time.time() - start_time
        self.val_history["learning_rate"].append(self.do_learning_rate_decay())
        self.val_history["duration"].append(elapsed_time)

        # Save validation history
        with open(self.save_path, 'w') as f:
            f.write(json.dumps(self.val_history))

    def federated_learning(self, fraction, max_rounds, model_type):
        weights = self.get_initial_weights(model_type)
        num_clients = max( ceil(fraction * len(self.clients)), 1 )
        self.best_accuracy = 0.0
        goal_accuracy = self.config["goal_accuracy"]

        @ray.remote
        def train_model(client, weights, config):
            return client.train(weights, config)

        ray.init(num_cpus=num_clients + 1)
        for t in range(1, max_rounds + 1):
            if self.best_accuracy > goal_accuracy:
                logging.info("Reached goal accuracy of {0} at round {1}."\
                    .format(goal_accuracy, t))
                break
            start_time = time.time()
            logging.info('Round number {0}.'.format(t+1))
            random_clients = random.sample(self.clients, num_clients)
            threads = ray.get([train_model.remote(c, weights, self.config) for c in random_clients])

            weights, n = threads[0]
            if num_clients > 1:
                for result in threads[1:]:
                    update, num_data = result
                    update = self.model.scale_weights(update, num_data)
                    weights = self.model.sum_weights(weights, update)
                    n += num_data
                weights = self.model.inverse_scale_weights(weights, n)

            # TODO: This could happen in parallel.
            eval_results = self.validate_model(t + 1, weights, start_time)

        logging.info("Final validation accuracy: {0}.".format(self.best_accuracy))
        logging.info("Saved results at {0}.".format(self.save_path))
        logging.info("----- Federated Learning Completed -----")

    def do_learning_rate_decay(self):
        self.config["learning_rate"] *= self.config["lr_decay"]
        logging.info("Learning rate after decay: {0}.".format(self.config["learning_rate"]))
        return self.config["learning_rate"]

    def get_checkpoints_folder(self):
        return "./checkpoints/" + self.model_type + '/'

    def get_latest_checkpoint(self):
        return tf.train.latest_checkpoint(self.get_checkpoints_folder())
