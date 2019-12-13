import os
import math
import numpy as np
import pandas as pd
import keras
import warnings


def count_datapoints(dataset_path):
    """
    Counts and returns the number of datapoints in the `dataset_path` directory.
    One line in a file inside the directory is equivalent to one datapoint.
    """
    assert os.path.isdir(dataset_path), "Dataset path is invalid."

    mappings = {}
    for filename in os.listdir(dataset_path):
        count = 0
        if not filename.endswith(".csv"): continue
        full_path = os.path.join(dataset_path, filename)
        with open(full_path, 'r') as f:
            for line in f:
                count += 1
        count -= 1 #exclude header
        mappings[filename] = count
    return mappings

def create_sequential_train_dataset_iterator(dataset_path, count, split=0.8, \
    batch_size=1, labeler=None, infinite=True):
    """
    Returns a sequential iterator of batches of size B containing all features
    of the data.

    Assumes `dataset_path` is a path to a folder with multiple CSV files.
    """
    if infinite:
        while True:
            yield from _create_sequential_dataset_iterator(dataset_path, \
                count*split, "train", batch_size, labeler)
    else:
        yield from _create_sequential_dataset_iterator(dataset_path, \
            count*split, "train", batch_size, labeler)

def create_sequential_test_dataset_iterator(dataset_path, count, split=0.2, \
    batch_size=1, labeler=None, infinite=True):
    """
    Returns a sequential iterator of batches of size B containing all features
    of the data.

    Assumes `dataset_path` is a path to a folder with multiple CSV files.
    """
    if infinite:
        while True:
            yield from _create_sequential_dataset_iterator(dataset_path, \
                count*split, "test", batch_size, labeler)
    else:
        yield from _create_sequential_dataset_iterator(dataset_path, \
            count*split, "test", batch_size, labeler)

def create_random_train_dataset_iterator(dataset_path,  batch_size=1, \
    labeler=None, infinite=True, num_epochs=1):
    """
    Returns an random iterator of batches of size B containing all features of
    the data.

    Assumes `dataset_path` is a path to a folder with multiple CSV files.
    """
    if infinite:
        while True:
            yield from _create_randomized_dataset_iterator(dataset_path, 
                batch_size, labeler)
    else:
        for _ in range(num_epochs):
            yield from _create_randomized_dataset_iterator(dataset_path,
                batch_size, labeler)

def create_random_test_dataset_iterator(dataset_path, batch_size=1, \
    labeler=None, infinite=True):
    """
    Returns a random iterator of batches of size B containing all features of
    the data.

    Assumes `dataset_path` is a path to a folder with multiple CSV files.
    """
    if infinite:
        while True:
            yield from _create_randomized_dataset_iterator(dataset_path, \
                batch_size, labeler)
    else:
        yield from _create_randomized_dataset_iterator(dataset_path, \
            batch_size, labeler)

def reverse_readline(filename, buf_size=8192):
    """
    A generator that returns the lines of a file in reverse order
    Obtained from: 
    https://stackoverflow.com/questions/2301789/read-a-file-in-reverse-order-using-python
    """
    with open(filename) as fh:
        segment = None
        offset = 0
        fh.seek(0, os.SEEK_END)
        file_size = remaining_size = fh.tell()
        while remaining_size > 0:
            offset = min(file_size, offset + buf_size)
            fh.seek(file_size - offset)
            buffer = fh.read(min(remaining_size, buf_size))
            remaining_size -= buf_size
            lines = buffer.split('\n')
            # the first line of the buffer is probably not a complete line so
            # we'll save it and append it to the last line of the next buffer
            # we read
            if segment is not None:
                # if the previous chunk starts right from the beginning of line
                # do not concact the segment to the last line of new chunk
                # instead, yield the segment first 
                if buffer[-1] is not '\n':
                    lines[-1] += segment
                else:
                    yield segment
            segment = lines[0]
            for index in range(len(lines) - 1, 0, -1):
                if len(lines[index]):
                    yield lines[index]
        # Don't yield None if the file was empty
        if segment is not None:
            yield segment

def _create_sequential_dataset_iterator(dataset_path, max_count, iter_type, \
    batch_size, labeler):
    """
    Returns a sequential iterator of batches of size B containing all features
    of the data. If batch_size > max_count, then the datapoints for the dataset 
    will be single batch of data (the iterator only iterates over one item.
    
    Assumes `dataset_path` is a path to a folder with multiple CSV files.
    
    NOTE: labeler is now a string that refers to a column name. Also, this
    method creates an iterator by sequentially iterating over data points
    (no randomization in the training-test split)
    """
    assert iter_type in ['train', 'test'], "'iter_type' parameter is invalid."
    assert os.path.isdir(dataset_path), "Dataset path is invalid."
    assert batch_size > 0, "Invalid batch size provided."
    if iter_type == 'train':
        directories = os.listdir(dataset_path)
    elif iter_type == 'test':
        directories = reversed(os.listdir(dataset_path))
    count = 0
    batch = []
    for filename in directories:
        if not filename.endswith(".csv"): continue
        full_path = os.path.join(dataset_path, filename)
        if iter_type == 'test':
            f = reverse_readline(full_path)
        else:
            f = open(full_path)
        next(iter(f)) #first line contains header, so ignore it
        for line in f:
            if len(batch) == batch_size:
                if batch_size == 1:
                    tup = batch[0]
                    yield (np.expand_dims(tup[0], axis=0), \
                        np.expand_dims(tup[1], axis=0))
                else:
                    X_list, y_list = list(), list()
                    for x, _ in batch: X_list.append(x)
                    for _, y in batch: y_list.append(y)
                    yield (np.array(X_list), np.array(y_list))
                batch = []

            if count >= max_count:
                if batch_size == 1:
                    tup = batch[0]
                    yield (np.expand_dims(tup[0], axis=0), \
                        np.expand_dims(tup[1], axis=0))
                else:
                    X_list, y_list = list(), list()
                    for x, _ in batch: X_list.append(x)
                    for _, y in batch: y_list.append(y)
                    yield (np.array(X_list), np.array(y_list))
                return
                
            line = line.split(",")
            assert labeler >= 0 and labeler < len(line), "Labeler is out of bounds."
            line = line[0:labeler] + line[labeler + 1:], line[labeler]
            batch.append(line)
            count += 1

def _create_randomized_dataset_iterator(dataset_path, batch_size, labeler):
    """
    Returns a randomized iterator of batches of size B containing all features
    of the data. If batch_size > max_count, then the datapoints for the 
    dataset will be single batch of data (the iterator only iterates over one
    item.

    Assumes `dataset_path` is a path to a folder with multiple CSV files.

    NOTE: labeler is now a string that refers to the column name

    Args:
        dataset_path (str): The dataset path to the actual file
        batch_size (int): Maximum number of datapoints in each batch
        labeler (str): Column name of column that is label

    Yields:
        tuple(X,y) where X is batch of features, y is batch of labels
    """
    if not labeler:
        labeler = "label"

    assert os.path.isfile(dataset_path), "Dataset path is invalid."
    assert batch_size > 0, "Invalid batch size provided."
    dataset = pd.read_csv(dataset_path).sample(frac=1) #Loads data and shuffles
    assert labeler in dataset.columns, 'Labeler is invalid.'

    # Calculate number of batches so that each batch is at most size
    # batch_size, and then create the batches and yield each one.
    
    count = len(dataset)
    batch_size = min(count, batch_size) 
    offset = count % batch_size
    leftover = []
    if offset:
        dataset, leftover = dataset.iloc[0:-offset], [dataset.iloc[-offset:]]
    num_batches = count/batch_size
    dataset_batches = np.array_split(dataset, num_batches) + leftover
    for batch in dataset_batches:
        yield (batch.drop(labeler, axis=1).values, pd.DataFrame(batch[labeler]).values)