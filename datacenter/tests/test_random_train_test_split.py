import pandas as pd
import os
import pytest
import random

from data.iterators import count_datapoints
from data.iterators import create_random_test_dataset_iterator
from data.iterators import create_random_train_dataset_iterator


@pytest.fixture(scope='session')
def dataset_path():
    return "tests/artifacts/iterators/random"

@pytest.fixture(scope='session')
def train_dataset_path():
    return "tests/artifacts/iterators/random/train.csv"

@pytest.fixture(scope='session')
def test_dataset_path():
    return "tests/artifacts/iterators/random/test.csv"

def get_num_columns(dataset_path):
    """
    Helper function to find the number of columns in dataset
    """
    for filename in os.listdir(dataset_path):
        if not filename.endswith(".csv"): continue
        full_path = os.path.join(dataset_path, filename)
        f = open(full_path)
        return len(list(f)[0].split(','))

def test_train_test_split(dataset_path, train_dataset_path, test_dataset_path):
    """
    Test train-test split works by:
        1. Checking the split put the right number of datapoints (proportional 
           to the total number) in the training and test datasets.
        2. Checking that datapoints don't overlap between each dataset
    """
    count = count_datapoints(dataset_path)

    #Set up iterator for training set
    random_train_iterator = create_random_train_dataset_iterator(
            train_dataset_path,
            batch_size=7,
            labeler='label',
            infinite=False 
        )

    #Set up iterator for test set.
    random_test_iterator = create_random_test_dataset_iterator(
            test_dataset_path,
            batch_size=7,
            labeler='label',
            infinite=False
        )

    #Collect "datapoints" for training and test set. In reality, just take the 
    #index so that overlapping points can be detected later.
    train_data = []
    for X,y in random_train_iterator:
        for datapoint in X:
            train_data.append(datapoint[-1])

    test_data = []
    for X,y in random_test_iterator:
        for datapoint in X:
            test_data.append(datapoint[-1])

    #Check that training set and test set have right number of datapoints
    assert len(train_data) == 0.8*count
    assert len(test_data) == 0.2*count

    #Set up dataframe for join
    train_df = pd.DataFrame(data={"index": train_data})
    test_df = pd.DataFrame(data={"index": test_data})

    #Check for no overlapping datapoints
    assert len(pd.merge(train_df, test_df, on='index').index) == 0

def test_large_batch_size(dataset_path, train_dataset_path, test_dataset_path):
    """
    Same as above, except test with batch_size > count (datapoints)
    """
    count = count_datapoints(dataset_path)
    batch_size = count * random.randint(1, 5)

    #Set up iterator for training set
    random_train_iterator = create_random_train_dataset_iterator(
            train_dataset_path,
            batch_size=batch_size,
            labeler='label',
            infinite=False 
        )

    #Set up iterator for test set.
    random_test_iterator = create_random_test_dataset_iterator(
            test_dataset_path,
            batch_size=batch_size,
            labeler='label',
            infinite=False
        )
    
    #Collect "datapoints" for training and test set. In reality, just take the 
    #index so that overlapping points can be detected later.
    train_data = []
    for X,y in random_train_iterator:
        for datapoint in X:
            train_data.append(datapoint[-1])

    test_data = []
    for X,y in random_test_iterator:
        for datapoint in X:
            test_data.append(datapoint[-1])

    #Check that training set and test set have right number of datapoints
    assert len(train_data) == 0.8*count
    assert len(test_data) == 0.2*count

    #Set up dataframe for join
    train_df = pd.DataFrame(data={"index": train_data})
    test_df = pd.DataFrame(data={"index": test_data})

    #Check for no overlapping datapoints
    assert len(pd.merge(train_df, test_df, on='index').index) == 0

def test_infinite_works(dataset_path, train_dataset_path, test_dataset_path):
    """
    With infinite=True, test 3 * count iterations to see that data is what we expect.
    """

    count = count_datapoints(dataset_path)

    #Set up iterator for training set
    random_train_iterator = create_random_train_dataset_iterator(
            train_dataset_path,
            batch_size=4,
            labeler='label',
            infinite=True
        )

    #Set up iterator for test set.
    random_test_iterator = create_random_test_dataset_iterator(
            test_dataset_path,
            batch_size=4,
            labeler='label',
            infinite=True
        )

    #Collect "datapoints" for training and test set. In reality, just take the 
    #index so that overlapping points can be detected later.
    limit = 3 * count

    num_datapoints = 0
    train_data = []
    for X,y in random_train_iterator:
        for datapoint in X:
            train_data.append(datapoint[-1])
            num_datapoints += 1
        if num_datapoints >= limit * 0.8:
            break

    num_datapoints = 0
    test_data = []
    for X,y in random_test_iterator:
        for datapoint in X:
            test_data.append(datapoint[-1])
            num_datapoints += 1
        if num_datapoints >= limit * 0.2:
            break

    #Check that training set and test set have right number of datapoints
    assert len(train_data) == 0.8*count*3
    assert len(test_data) == 0.2*count*3

    #Set up dataframe for join
    train_df = pd.DataFrame(data={"index": train_data})
    test_df = pd.DataFrame(data={"index": test_data})

    #Check for no overlapping datapoints
    assert len(pd.merge(train_df, test_df, on='index').index) == 0

def test_invalid_batch_size(dataset_path, train_dataset_path, test_dataset_path):
    """
    Test that assertion fails with invalid batch size.
    """
    count = count_datapoints(dataset_path)
    
    #Set up iterator for training set
    random_train_iterator = create_random_train_dataset_iterator(
            train_dataset_path,
            batch_size=-1,
            labeler='label',
            infinite=False 
        )

    #Set up iterator for test set.
    random_test_iterator = create_random_test_dataset_iterator(
            test_dataset_path,
            batch_size=-1,
            labeler='label',
            infinite=False
        )

    #Assertion should fail here.
    try:
        train_data = []
        for X,y in random_train_iterator:
            for datapoint in X:
                train_data.append(datapoint[-1])
        assert False,"Assertion for batch size should have failed"
    except AssertionError as e:
        assert str(e) == "Invalid batch size provided."

def test_invalid_labeler(dataset_path, train_dataset_path, test_dataset_path):
    """
    Test that assertion fails with invalid labeler.
    """
    count = count_datapoints(dataset_path)

    #Set up iterator for training set
    random_train_iterator = create_random_train_dataset_iterator(
            train_dataset_path,
            batch_size=4,
            labeler='bad_column',
            infinite=True
        )

    #Set up iterator for test set.
    random_test_iterator = create_random_test_dataset_iterator(
            test_dataset_path,
            batch_size=4,
            labeler='bad_column',
            infinite=True
        )

    #Assertion should fail here.
    try:
        train_data = []
        for X,y in random_train_iterator:
            for datapoint in X:
                train_data.append(datapoint[-1])
        assert False,"Assertion for labeler should have failed."
    except AssertionError as e:
        assert str(e) == "Labeler is invalid."

def test_invalid_dataset_path():
    dataset_path = "bad/dataset/path"
    try:
        count_datapoints(dataset_path)
        assert False, "Assertion for dataset path should have failed."
    except AssertionError as e:
        assert(str(e) == "Dataset path is invalid.")
