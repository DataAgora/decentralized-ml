import os

import numpy as np
from keras.models import Sequential, load_model
from keras.layers import LSTM, Dropout, TimeDistributed, Dense, Activation, Embedding
from keras import optimizers

from models.generic_model import GenericKerasModel


class LSTMModel(GenericKerasModel):
    def __init__(self):
        self.embedding_size = 8
        self.n_hidden = 256
        self.seq_len = 80
        self.embed_path = './models/char-embeds.txt'
        self.embedding_matrix, self.char_to_idx, self.vocab_size = \
            self.build_embed_matrix()
        self.model = self.build_model()

    def build_embed_matrix(self):
        chars = set()
        embeds = {}
        with open(self.embed_path, 'r') as f:
            for line in f:
                line_split = line[2:].split(" ")
                vec = np.array(line_split, dtype=float)
                char = line[0]
                # TODO: Find a better way to read \n from the .txt
                # (at the moment ` replaces \n)
                if char == '`':
                    char = '\n'
                embeds[char] = vec
                chars.add(char)

        char_indices = dict((c, i) for i, c in enumerate(sorted(chars)))

        embedding_matrix = np.zeros((len(chars), self.embedding_size))
        for char, i in char_indices.items():
            embedding_vector = embeds.get(char)
            if embedding_vector is not None:
                embedding_matrix[i] = embedding_vector

        return embedding_matrix, char_indices, embedding_matrix.shape[0]

    def build_model(self):
        model = Sequential()
        model.add(Embedding(self.vocab_size, self.embedding_size, trainable=False,
            weights=[self.embedding_matrix], batch_input_shape=(None, self.seq_len)))
        model.add(LSTM(self.n_hidden, return_sequences=True, unroll=True))
        model.add(LSTM(self.n_hidden, return_sequences=True, unroll=True))
        model.add(TimeDistributed(Dense(self.vocab_size)))
        model.add(Activation('softmax'))
        model.summary()
        return model

    def build_optimizer(self, learning_rate):
        sgd = optimizers.SGD(lr=learning_rate)
        self.model.compile(loss='categorical_crossentropy', optimizer=sgd, metrics=['accuracy'])

    def train(self, text, config):
        self.epochs = config['epochs']
        self.batch_size = config['batch_size']
        for epoch in range(self.epochs):
            losses, accs = [], []
            for i, (X, Y) in enumerate(self.read_batches(text)):
                loss, acc = self.model.train_on_batch(X, Y)
                print('Batch {}: loss = {}, acc = {}'.format(i + 1, loss, acc))
                losses.append(loss)
                accs.append(acc)
        print("Training complete.")

    def read_batches(self, T):
        T = []
        for c in text:
            if c == '\t': c = ' '
            T.append(self.char_to_idx[c])
        T = np.asarray(T, dtype=np.int32)
        length = T.shape[0]
        batch_chars = length // self.batch_size

        for start in range(0, batch_chars - self.seq_len, self.seq_len):
            X = np.zeros((self.batch_size, self.seq_len))
            Y = np.zeros((self.batch_size, self.seq_len, self.vocab_size))
            for batch_idx in range(0, self.batch_size):
                for i in range(0, self.seq_len):
                    X[batch_idx, i] = T[batch_chars * batch_idx + start + i]
                    Y[batch_idx, i, T[batch_chars * batch_idx + start + i + 1]] = 1
            yield X, Y

    def validate(self, text):
        # TODO: Need to implement.
        pass


if __name__ == '__main__':
    with open('datasets/shakespeare.txt', 'r') as f:
        text = f.read()
    m = LSTMModel()
    m.build_optimizer(1.47)
    m.train(text, {"epochs":1, "batch_size":8})
