import numpy as np
import tensorflow as tf

from models.generic_model import GenericTensorflowModel

class CNN(GenericTensorflowModel):
    def __init__(self):
        self.n_channels1 = 32
        self.kernel_size1 = (5, 5)
        self.n_channels2 = 64
        self.kernel_size2 = (5, 5)
        self.n_hidden = 512
        self.n_classes = 10

    def preprocess_input(self, x):
        x = tf.cast(x, tf.float32)
        # TODO: Implement pre-process for CIFAR10.
        return x

    def preprocess_labels(self, labels):
        labels = tf.cast(labels, tf.int32)
        return labels

    def build_model(self, input_layer):
        new_weights = self.new_weights if hasattr(self, 'new_weights') else None
        get_conv_tensor_name = lambda l, t: new_weights['/'.join([l, "conv2d", t]) + ":0"]
        get_dense_tensor_name = lambda l, t: new_weights['/'.join([l, "dense", t]) + ":0"]

        layer_name = "conv_layer1"
        with tf.variable_scope(layer_name):
            kernel_init, bias_init = None, None
            if new_weights:
                kernel_init = tf.constant_initializer(get_conv_tensor_name(layer_name, "kernel"))
                bias_init = tf.constant_initializer(get_conv_tensor_name(layer_name, "bias"))
            self.out = tf.layers.conv2d(input_layer, self.n_channels1, self.kernel_size1,
                activation=tf.nn.relu, kernel_initializer=kernel_init, bias_initializer=bias_init)

        self.out = tf.layers.max_pooling2d(inputs=self.out, pool_size=[2, 2], strides=2)

        layer_name = "conv_layer2"
        with tf.variable_scope(layer_name):
            kernel_init, bias_init = None, None
            if new_weights:
                kernel_init = tf.constant_initializer(get_conv_tensor_name(layer_name, "kernel"))
                bias_init = tf.constant_initializer(get_conv_tensor_name(layer_name, "bias"))
            self.out = tf.layers.conv2d(self.out, self.n_channels2, self.kernel_size2,
                activation=tf.nn.relu, kernel_initializer=kernel_init, bias_initializer=bias_init)


        self.out = tf.layers.max_pooling2d(inputs=self.out, pool_size=[2, 2], strides=1)

        self.out = tf.layers.flatten(self.out)

        layer_name = "dense_layer"
        with tf.variable_scope(layer_name):
            kernel_init, bias_init = None, None
            if new_weights:
                kernel_init = tf.constant_initializer(get_dense_tensor_name(layer_name, "kernel"))
                bias_init = tf.constant_initializer(get_dense_tensor_name(layer_name, "bias"))
            self.out = tf.layers.dense(self.out, self.n_hidden, tf.nn.relu,
                kernel_initializer=kernel_init, bias_initializer=bias_init)

        layer_name = "logits_layer"
        with tf.variable_scope(layer_name):
            kernel_init, bias_init = None, None
            if new_weights:
                kernel_init = tf.constant_initializer(get_dense_tensor_name(layer_name, "kernel"))
                bias_init = tf.constant_initializer(get_dense_tensor_name(layer_name, "bias"))
            self.logits = tf.layers.dense(self.out, self.n_classes,
                kernel_initializer=kernel_init, bias_initializer=bias_init)

    def build_loss(self):
        self.loss = tf.losses.sparse_softmax_cross_entropy(
            labels=self.labels,
            logits=self.logits,
            loss_collection=tf.GraphKeys.LOSSES
        )

    def build_optimizer(self):
        optimizer = tf.train.GradientDescentOptimizer(learning_rate=self.learning_rate)
        self.optimizer = optimizer.minimize(
            loss=self.loss,
            global_step=tf.train.get_global_step(),
            name='train_op'
        )

    def build_predictions_obj(self):
        logits = self.logits
        classes = tf.argmax(input=self.logits, axis=1, name="classes_tensor")
        probabilities = tf.nn.softmax(self.logits, name="softmax_tensor")

        tf.add_to_collection('predictions', logits)
        tf.add_to_collection('predictions', classes)
        tf.add_to_collection('predictions', probabilities)

        self.predictions = {
            "logits": logits,
            "classes": classes,
            "probabilities": probabilities
        }

    def build_eval_metric(self):
        self.eval_metric_ops = {
          "accuracy": tf.metrics.accuracy(labels=self.labels, predictions=self.predictions["classes"])
        }

    def get_estimator(self, mode):
        estimator = None
        self.build_predictions_obj()
        if mode == tf.estimator.ModeKeys.PREDICT:
            self.build_eval_metric()
            estimator = tf.estimator.EstimatorSpec(mode=mode, predictions=self.predictions)
        elif mode == tf.estimator.ModeKeys.TRAIN:
            self.build_loss()
            self.build_optimizer()
            estimator = tf.estimator.EstimatorSpec(mode=mode, loss=self.loss, train_op=self.optimizer)
        elif mode == tf.estimator.ModeKeys.EVAL:
            self.build_loss()
            self.build_eval_metric()
            estimator = tf.estimator.EstimatorSpec(mode=mode, loss=self.loss, eval_metric_ops=self.eval_metric_ops)
        return estimator

    def get_model(self, features, labels, mode, params):
        """
        When using the Estimator API, features will come as a TF Tensor already.
        """
        # Set up hyperparameters.
        if params:
            self.learning_rate = params.get("learning_rate", None)
            self.new_weights = params.get("new_weights", None)

        # Do pre-processing if necessary.
        self.input_layer = self.preprocess_input(features["x"])
        self.labels = labels
        if labels != None:
            self.labels = self.preprocess_labels(labels)

        # Define the model.
        self.build_model(self.input_layer)

        # Build and return the estimator.
        return self.get_estimator(mode)
