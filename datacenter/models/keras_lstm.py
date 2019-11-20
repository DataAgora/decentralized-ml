# Add the parent directory to the PATH to allow imports.
import os, sys, inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)

import numpy as np
import keras
from keras.models import Sequential
from keras.layers import LSTM, Dense
from keras import optimizers

from models.generic_model import GenericKerasModel


class KerasLSTM(GenericKerasModel):
    def __init__(self, is_training=False):
        # self.n_input = 784
        # self.n_hidden1 = 200
        # self.n_hidden2 = 200
        # self.n_classes = 10
        self.is_training = is_training
        self.model = self.build_model()
        if is_training:
            self.compile_model()

    def build_model(self):
        model = Sequential()
        model.add(LSTM(160, input_shape = (1, 686), return_sequences=True))
        model.add(LSTM(200))
        model.add((Dense(1)))
        model.summary()
        return model

    def compile_model(self):
        self.model.compile(loss='mean_squared_error', optimizer='adam', metrics=['mape'])



if __name__ == '__main__':
    from data.iterators import count_datapoints
    from data.iterators import create_train_dataset_iterator
    from data.iterators import create_test_dataset_iterator
    from examples.labelers import lstm_labeler

    # Constants
    data_count = 1000
    split = 0.8
    batch_size = 500
    epochs = 2

    # Model definition
    m = KerasLSTM(is_training=True)

    # Training
    dataset_iterator = create_train_dataset_iterator('datasets/power', data_count, \
        split=split, batch_size=batch_size, labeler=lstm_labeler)
    hist = m.model.fit_generator(dataset_iterator, epochs=epochs, \
        steps_per_epoch=(data_count*split)//batch_size)
    train_history = hist.history
    print(train_history)

    # Validation
    dataset_iterator = create_test_dataset_iterator('datasets/power', data_count, \
        split=split, batch_size=batch_size, labeler=lstm_labeler)
    hist = m.model.evaluate_generator(dataset_iterator, \
        steps=(data_count*(1-split))//batch_size)
    val_history = dict(zip(m.model.metrics_names, hist))
    print(val_history)
