import time
import uuid
import os
import boto3

import state
from model import TEMP_FOLDER, get_current_h5_model_path


def store_update(type, message, with_weights=True):
    """
    Stores an update in DynamoDB. If weights are present, it stores them in S3.
    """

    print("[{0}]: {1}".format(type, message))

    access_key = os.environ["ACCESS_KEY_ID"]
    secret_key = os.environ["SECRET_ACCESS_KEY"]
    if with_weights:
        try:
            repo_id = state.state['repo_id']
            session_id = state.state['session_id']
            round = state.state['current_round']
            s3 = boto3.resource('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_key)
            weights_s3_key = '{0}/{1}/{2}/model.h5'.format(repo_id, session_id, round)
            object = s3.Object('updatestore', weights_s3_key)
            h5_filepath = state.state['h5_model_path']
            print(h5_filepath)
            print(os.listdir())
            object.put(Body=open(h5_filepath, 'rb'))
        except Exception as e:
            print("S3 Error: {0}".format(e))

    try:
        dynamodb = boto3.resource('dynamodb', region_name='us-west-1', aws_access_key_id=access_key, aws_secret_access_key=secret_key)
        table = dynamodb.Table("UpdateStore")
        item = {
            'Id': str(uuid.uuid4()),
            'RepoId': state.state["repo_id"],
            'Timestamp': int(time.time()),
            'ContentType': type,
            'SessionId': state.state["session_id"],
            'Content': repr(message),
        }
        print(item)
        if with_weights:
            item['WeightsS3Key'] = "s3://updatestore/" + weights_s3_key
        table.put_item(Item=item)
    except Exception as e:
        print("DB Error: {0}".format(e))
