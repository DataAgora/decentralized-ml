import logging

import numpy as np
import tensorflow as tf
from keras import backend as K


class GenericModel:
    """
    Generic Tensorflow Model Class

    Each subclass of this class needs to define the data structure of its weights
    (which should be respected accross methods) and implement the functions below.

    """

    def get_model(self):
        raise NotImplementedError("Subclasses should implement this!")

    def load_weights(self):
        raise NotImplementedError("Subclasses should implement this!")

    def get_weights(self):
        raise NotImplementedError("Subclasses should implement this!")

    def sum_weights(self, weights1, weights2):
        raise NotImplementedError("Subclasses should implement this!")

    def scale_weights(self, weights, factor):
        raise NotImplementedError("Subclasses should implement this!")

    def inverse_scale_weights(self, weights, factor):
        raise NotImplementedError("Subclasses should implement this!")


class GenericTensorflowModel(GenericModel):
    def load_weights(self, new_weights, latest_checkpoint, checkpoint_dir):
        tf.reset_default_graph()
        with tf.Session().as_default() as sess:
            new_saver = tf.train.import_meta_graph(latest_checkpoint + '.meta')
            # To load non-trainable variables and prevent errors...
            # we restore them if they are found, or initialize them otherwise.
            try:
                new_saver.restore(sess, latest_checkpoint)
            except:
                sess.run(tf.global_variables_initializer())

            collection = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES)
            for tensor in collection:
                assign_op = tensor.assign(new_weights[tensor.name])
                sess.run(assign_op)

            save_path = new_saver.save(sess, checkpoint_dir + "model.ckpt")
        tf.reset_default_graph()

    def get_weights(self, latest_checkpoint):
        tf.reset_default_graph()
        graph = tf.Graph()
        with tf.Session(graph=graph) as sess:
            new_saver = tf.train.import_meta_graph(latest_checkpoint + '.meta')
            new_saver.restore(sess, latest_checkpoint)
            collection = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES)
            weights = {tensor.name:sess.run(tensor) for tensor in collection}
        return weights

    def sum_weights(self, weights1, weights2):
        new_weights = {}
        for key1, key2 in zip(sorted(weights1.keys()), sorted(weights2.keys())):
            assert key1 == key2, 'Error with keys'
            new_weights[key1] = weights1[key1] + weights2[key2]
        return new_weights

    def scale_weights(self, weights, factor):
        new_weights = {}
        for key, value in weights.items():
            new_weights[key] = value * factor
        return new_weights

    def inverse_scale_weights(self, weights, factor):
        new_weights = {}
        for key, value in weights.items():
            new_weights[key] = value / factor
        return new_weights


class GenericKerasModel(GenericModel):
    def set_weights(self, new_weights):
        self.model.set_weights(new_weights)

    def get_weights(self):
        return self.model.get_weights()

    def get_initial_weights(self):
        model = self.build_model()
        return model.get_weights()

    def sum_weights(self, weights1, weights2):
        new_weights = []
        for w1, w2 in zip(weights1, weights2):
            new_weights.append(w1 + w2)
        return new_weights

    def scale_weights(self, weights, factor):
        new_weights = []
        for w in weights:
            new_weights.append(w * factor)
        return new_weights

    def inverse_scale_weights(self, weights, factor):
        new_weights = []
        for w in weights:
            new_weights.append(w / factor)
        return new_weights
