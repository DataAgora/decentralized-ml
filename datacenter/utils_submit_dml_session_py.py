#!/usr/bin/env python

import json
import requests

import ipfsapi

from tests.testing_utils import make_serialized_job

serialized_job = make_serialized_job("bleh")
serialized_job["job_data"]["hyperparams"]["batch_size"] = 32
serialized_job["job_data"]["hyperparams"]["epochs"] = 100
# client one corresponds to artifacts/integration/configuration.ini
# client one corresponds to tests/artifacts/integration
# client two corresponds to artifacts/integration/configuration2.ini
# client two corresponds to tests/artifacts/datasets
mnist_uuid = '0fcf9cbb-39df-4ad6-9042-a64c87fecfb3'
mnist_uuid_2 = 'd16c6e86-d103-4e71-8741-ee1f888d206c'
new_session_key = {"dataset_uuid": mnist_uuid, "label_column_name": "label"}
new_session_key_2 = {"dataset_uuid": mnist_uuid_2, "label_column_name": "label"}
new_session_event = {
        "optimizer_params": {"num_averages_per_round": 0, "max_rounds": 5},
        "serialized_job": serialized_job,
        "participants": [mnist_uuid]
        # "participants": ['0fcf9cbb-39df-4ad6-9042-a64c87fecfb3', 
        #                 'd16c6e86-d103-4e71-8741-ee1f888d206c']
}

client = ipfsapi.connect('127.0.0.1', 5001)
content_hash = client.add_json(new_session_event)
key_hash = client.add_json(new_session_key)
key_hash_2 = client.add_json(new_session_key_2)
assert key_hash != key_hash_2
headers = {
    "Content-Type": "application/json",
}

data = {
    "KEY": str(key_hash),
    "CONTENT": str(content_hash),
}
r = requests.post(
    'http://127.0.0.1:3000/txs',
    headers=headers,
    data=json.dumps(data),
)
data_2 = {
    "KEY": str(key_hash_2),
    "CONTENT": str(content_hash),
}
assert data != data_2
r_2 = requests.post(
    'http://127.0.0.1:3000/txs',
    headers=headers,
    data=json.dumps(data_2),
)
if r.status_code == requests.codes.ok:
    print("OK")
else:
    print("Error")
