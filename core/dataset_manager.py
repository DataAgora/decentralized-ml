import shutil
import logging
import datetime
import string
import random
import os
import yaml
import uuid

import numpy as np
import pandas as pd

import core.utils.context
from core.configuration import ConfigurationManager


logging.basicConfig(level=logging.INFO,
                format='[DatasetManager] %(asctime)s %(levelname)s %(message)s')

class DatasetManager():
    """
    Dataset Manager

    This class takes in an filepath to raw data upon initialization.
    Some functionalities include:

        1. Validating data.
        2. TODO: Detecting changes in data 
        3. TODO: Validating data after changes, validating only new data?

    Each instance corresponds to a set of raw data. The directory should look 
    something like this:

    main/
        dataset1/
            dataset1.csv
        dataset2/
            dataset2.csv

    The Dataset Manager will be initialized in the Bootstrapper. 
    """

    def __init__(self, config_manager):
        """
        Take in an filepath to the raw data.

        For now, throw an exception if a valid dataset path is not provided.

        TODO: In the event of a invalid dataset path, log a useful message 
        for the user and don't terminate the service

        TODO: Config Manager asks provider to label the data, but we need
        to eventually build a classifier that does this automatically. 
        """
        config = config_manager.get_config()
        raw_filepath = config['GENERAL']['dataset_path']
        assert os.path.isdir(raw_filepath), \
            "The dataset filepath provided is not valid."
        self._raw_filepath = raw_filepath
        self._mappings = None
        self._validate_data()
        self._port = config.getint("BLOCKCHAIN", "http_port")
        self._frac = float(config['DATASET_MANAGER']['sample_fraction'])
        self._ipfs_client = None
        self._db_client = None
        self.classification = config['DATASET_MANAGER']['category']

    def configure(self, ipfs_client, db_client):
        """
        Sets up IPFS client for _communicate.

        Sets up DB Client for pushing labels to DB.
        """
        self._ipfs_client = ipfs_client
        self._db_client = db_client
    
    def validate_key(self, key):
        return key in self.get_mappings().keys()
    
    def _validate_data(self):
        """
        Validate all raw data. As of now, checks that:
            1. Each dataset has a header. Assumes column names are always
               string. NOTE: if data is also string, then it is impossible
               to tell whether file has header or not.
            2. Each dataset is in a valid CSV format. pandas already
               performs this validation when it reads in CSV files, so just
               return the error from pandas if reading fails.
        """
        format_message = ("The file {file} in folder {folder} was improperly "
                          "formatted. Please refer to the following error "
                          "message from pandas for more information: {message}")
        header_message = ("No header has been provided in file {file} in "
                          "folder {folder}")
        for folder in os.listdir(self._raw_filepath):
            folder_path = os.path.join(os.path.abspath(self._raw_filepath), folder)
            if not os.path.isdir(folder_path): continue
            files = os.listdir(folder_path)
            for file in files:
                if not file.endswith(".csv"): continue
                if file[:2] == 'md': continue
                file_path = os.path.join(folder_path, file)
                try:
                    dataset = pd.read_csv(file_path, index_col=False)
                except Exception as e:
                    logging.error(str(e))
                    raise Exception(
                        format_message.format(
                            file=file,
                            folder=folder,
                            message=str(e)
                        )
                    )
                is_str = lambda c: not c.replace('.','',1).isdigit()
                assert all([is_str(c) for c in dataset.columns]), \
                    header_message.format(
                        file=file,
                        folder=folder
                    )
    
    def get_mappings(self):
        """
        Returns the dataset mappings.
        """
        if not self._mappings:
            raise Exception("Dataset Manager needs to be bootstrapped first.")
        return self._mappings

    def bootstrap(self):
        """
        Check if datasets.yaml exists. If so, load it into the class (if it
        hasn't been already). Otherwise, call _create_dataset_mappings

        Returns True if mappings had to be created, and False otherwise 
        (used for testing).
        """
        mapping_filepath = os.path.join(self._raw_filepath, "datasets.yaml")
        if os.path.isfile(mapping_filepath):
            if not self._mappings:
                with open(mapping_filepath, "r") as f:
                    self._mappings = yaml.load(f)
            return False
        else:
            self._create_dataset_mappings(mapping_filepath)
            return True
        
    def _create_dataset_mappings(self, mapping_filepath):
        """
        mapping_filepath is the filepath where datasets.yaml is created, which
        is <raw_filepath>/datasets.yaml.

        For each dataset folder in the raw_filepath, generate a random string
        using uuid and add a (key, value) pair to a dictionary such that the 
        random string is key and the dataset folder name is the value. Store
        the dictionary in _mappings and in a yaml file at mapping_filepath.

        Ultimately, we are assigning identifiers for each dataset.
        """
        mappings = {}
        for folder in os.listdir(self._raw_filepath):
            encoding = str(uuid.uuid4())
            mappings[encoding] = folder
        self._mappings = mappings
        with open(mapping_filepath, "w") as f:
            f.write(yaml.dump(mappings))

    def _generate_ed_directory(self):
        """
        This is a helper method that encompasses the logic for creating the
        ED Directory. Given the directory example in the class docstring, 
        an example of an ED Directory can look like this:

        {
            ...
            <dataset1_uuid> : (<dataset1 sample json>, <dataset1 metadata json>),
            <dataset2_uuid> : (<dataset2 sample json>, <dataset2 metadata json>)
            ...
        }
        """
        ed_directory = {}
        mappings = self._mappings
        filepath = os.path.join(self._raw_filepath, 'datasets.yaml')
        reverse_mappings = {v: k for k, v in mappings.items()}

        for folder in os.listdir(self._raw_filepath):
            folder_path = os.path.join(os.path.abspath(self._raw_filepath), folder)
            if not os.path.isdir(folder_path): continue
            encoding = reverse_mappings[folder]
            files = list(os.listdir(folder_path))
            assert len(files) == 1, \
                "We only support one file per dataset folder!"
            file_name = files[0]
            if not file_name.endswith(".csv"): continue
            filepath = os.path.join(folder_path, file_name)
            dataset = pd.read_csv(filepath)
            sample = dataset.sample(frac=self._frac)
            metadata = dataset.describe()
            ed_directory[encoding] = (sample.to_json(), metadata.to_json())
        
        return ed_directory

    def post_directories_and_category_labels(self, key):
        """
        Post the ED Directory on blockchain with the given key.

        The ED Directory is a JSON dictionary whose keys represent the dataset
        folders in the directory and whose values represent the corresponding
        datasets. Assume only one dataset file per folder. 

        See _generate_ed_directory docstring for an example of what an ED
        Directory looks like.
        """
        assert len(key) <= 30, \
            "Keys for datasets can only be at most 30 characters long."
        assert self._db_client, \
            "DB client has not been set. Dataset Manager needs to be configured!"
        assert self._ipfs_client, \
            "IPFS client has not been set. Dataset Manager needs to be configured!"
        
        ed_directory = self._generate_ed_directory()

        self._db_client.add_classifications([key], [self.classification])

        receipt = setter(
                    client=self._ipfs_client, 
                    key=key, 
                    value=ed_directory, 
                    port=self._port
                )
        return receipt
