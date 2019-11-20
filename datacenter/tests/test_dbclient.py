import os
import tests.context
import psycopg2
import pytest
import pandas as pd
import string
import random
from core.db_client import DBClient
from core.configuration import ConfigurationManager


@pytest.fixture
def db_client():
    """
    Maintain instance of DB Client
    """
    config_manager = ConfigurationManager()
    config_manager.bootstrap(
        config_filepath='tests/artifacts/db_client/configuration.ini'
    )
    return DBClient(config_manager)

def check_empty_category_classifications(db_client):
    """
    Check that retrieving classifications works
    """
    expected = pd.DataFrame(columns=['data_provider', 'category'])
    actual = db_client._get_classifications()
    assert expected.equals(actual)

def check_add_works(db_client, data_provider):
    """
    Check that adding classifications works
    """
    actual = db_client._get_classifications()
    assert list(actual['data_provider'])[-1] == data_provider
    assert list(actual['category'])[-1] == 'social_media'

def check_get_data_providers_with_category(db_client, data_provider):
    """
    Check that retrieving classifications with specified category works.
    """
    actual = db_client._get_data_providers_with_category('social_media')
    assert list(actual['data_provider'])[-1] == data_provider
    assert list(actual['category'])[-1] == 'social_media'

def reset(db_client, data_provider_list):
    """
    Clean up before and after tests.
    """
    classifications = db_client._get_classifications()
    for data_provider in data_provider_list:
        classifications = classifications[classifications['data_provider'] != data_provider]
    classifications.to_sql(
        name=db_client.table_name, 
        con=db_client.db.engine, 
        if_exists='replace', 
        index=False
    )

def test_end_to_end(db_client):
    """
    NOTE: "get" tests sometimes fail because the table gets randomly
    deleted. The block of code below before random_string is a temporary fix.

    TODO: Why does the RDS DB keep deleting tables????
    """
    classifications = pd.DataFrame(columns=['category', 'data_provider'])
    classifications.to_sql(
        name=db_client.table_name, 
        con=db_client.db.engine, 
        if_exists='append', 
        index= False
    )

    def random_string(length):
        return ''.join(
            random.choice(string.ascii_letters) for m in range(length)
        ).lower()
    social_data_provider = random_string(10)
    fitness_data_provider = random_string(10)
    db_client.add_classifications([social_data_provider], ['social_media'])
    check_add_works(db_client, social_data_provider)
    db_client.add_classifications([fitness_data_provider], ['fitness'])
    check_get_data_providers_with_category(db_client, social_data_provider)
    reset(db_client, [social_data_provider, fitness_data_provider])
