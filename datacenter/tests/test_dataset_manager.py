import numpy as np
import pandas as pd
import os
import sys
import inspect
import tests.context
import pytest
import shutil

import ipfsapi

from core.blockchain.blockchain_utils import getter, setter
from core.configuration import ConfigurationManager
from core.dataset_manager import DatasetManager


@pytest.fixture(scope='session')
def good_config_manager():
    config_manager = ConfigurationManager()
    config_manager.bootstrap(
        config_filepath='tests/artifacts/dataset_manager/configuration.ini'
    )
    return config_manager

@pytest.fixture(scope='session')
def good_dataset_manager(good_config_manager):
    return DatasetManager(good_config_manager)

@pytest.fixture(scope='session')
def bad_config_manager_format():
    config_manager = ConfigurationManager()
    config_manager.bootstrap(
        config_filepath='tests/artifacts/dataset_manager/configuration2.ini'
    )
    return config_manager

@pytest.fixture(scope='session')
def bad_config_manager_header():
    config_manager = ConfigurationManager()
    config_manager.bootstrap(
        config_filepath='tests/artifacts/dataset_manager/configuration3.ini'
    )
    return config_manager

def test_no_header(bad_config_manager_header):
    """
    Test that DSM invalidates dataset with no header.
    """
    error_message = ("No header has been provided in file {file} in folder "
                     "{folder}")
    error_message = error_message.format(
                        file='test1.csv',
                        folder='test1',
                    )
    try:
        dataset_manager = DatasetManager(bad_config_manager_header)
        raise Exception("Error should have been thrown for lack of header")
    except AssertionError as e:
        assert str(e) == error_message, "Wrong assertion was thrown!"

def test_bad_format(bad_config_manager_format):
    """
    Test that DSM invalidates dataset with invalid CSV format.
    """
    format_message = ("The file {file} in folder {folder} was improperly "
                      "formatted. Please refer to the following error "
                      "message from pandas for more information: {message}")
    format_message = format_message.format(
                        file='test1.csv',
                        folder='test1',
                        message='list index out of range'
                     )                  
    try:
        dataset_manager = DatasetManager(bad_config_manager_format)
        raise Exception("Error should have been thrown for bad format")
    except Exception as e:
        assert str(e) == format_message, "Wrong assertion was thrown!"

def check_mappings_exist(dataset_manager):
    """
    Ensure that a yaml file was created.
    """
    assert dataset_manager.get_mappings()
    mapping_filepath = os.path.join(
        dataset_manager._raw_filepath, 
        'datasets.yaml'
    )
    assert os.path.isfile(mapping_filepath)

def check_mappings_correctness(dataset_manager):
    """
    Ensure that the values of the mappings are the folders in _raw_filepath
    """
    mappings = dataset_manager.get_mappings()
    folders = list(mappings.values())
    assert (folders[0] == 'test1' and folders[1] == 'test2') \
        or (folders[0] == 'test2' and folders[1] == 'test1'), \
        "Dataset mappings are incorrect!"

def clean_up(dataset_manager):
    """
    Remove datasets.yaml, if it exists.
    """
    mapping_filepath = os.path.join(
        dataset_manager._raw_filepath, 
        'datasets.yaml'
    )
    if os.path.isfile(mapping_filepath):
        os.remove(mapping_filepath)

def test_complete_yaml_creation(good_dataset_manager):
    """
    Verify datasets.yaml (dataset mappings) is created and correct.
    """
    good_dataset_manager.bootstrap()
    check_mappings_exist(good_dataset_manager)
    mappings = good_dataset_manager.get_mappings()
    check_mappings_correctness(good_dataset_manager)
    
    clean_up(good_dataset_manager)

def test_no_yaml_creation_repeat(good_dataset_manager):
    """
    Verify that _create_dataset_mappings is not run again when mappings
    already exist. 
    """
    good_dataset_manager.bootstrap()
    check_mappings_exist(good_dataset_manager)
    assert not good_dataset_manager.bootstrap(), \
        "Created mappings even though mappings already loaded!"

    good_dataset_manager._mappings = None
    assert not good_dataset_manager.bootstrap(), \
        "Created mappings even though datasets.yaml already exists!"
    
    clean_up(good_dataset_manager)

def test_ed_directory_format(good_dataset_manager):
    good_dataset_manager.bootstrap()
    ed_directory = good_dataset_manager._generate_ed_directory()
    filepath = os.path.join(good_dataset_manager._raw_filepath, 'datasets.yaml')
    mappings = good_dataset_manager._mappings

    assert type(ed_directory == dict), \
        "ED Directory is not a dictionary!"

    for encoding, data_tuple in ed_directory.items():
        dataset = data_tuple[0]
        assert encoding in mappings.keys(), \
            "Key is not encoding in dataset mappings!"
        
        df = pd.read_json(dataset)
        assert len(df) == 1, \
            "Sample was not 10 percent of original data!"

    clean_up(good_dataset_manager)

'''
uncomment when node is running
def test_bad_metadata_post():
    try:
        rfp = os.path.join(currentdir, 'artifacts/dataset_manager_test_data')
        dataset_manager = DatasetManager(rfp)
        dataset_manager.post_dataset_with_md("my_test")
        assert False
    except NoMetadataFoundError:
        pass
'''