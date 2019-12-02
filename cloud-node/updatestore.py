import time
import uuid
import os
import boto3

import state

access_key = os.environ["ACCESS_KEY_ID"]
secret_key = os.environ["SECRET_ACCESS_KEY"]

def store_update(type, message, with_weights=True):
    """
    Stores an update in DynamoDB. If weights are present, it stores them in S3.
    """
    print("[{0}]: {1}".format(type, message))

    if state.state["test"]:
        return
    
    if with_weights:
        try:
            repo_id = state.state["repo_id"]
            session_id = state.state["session_id"]
            round = state.state["current_round"]
            s3 = boto3.resource("s3", aws_access_key_id=access_key,
                aws_secret_access_key=secret_key)
            weights_s3_key = "{0}/{1}/{2}/model.h5"
            weights_s3_key = weights_s3_key.format(repo_id, session_id, round)
            object = s3.Object("updatestore", weights_s3_key)
            h5_filepath = state.state["h5_model_path"]
            object.put(Body=open(h5_filepath, "rb"))
        except Exception as e:
            print("S3 Error: {0}".format(e))

    try:
        dynamodb = boto3.resource("dynamodb", region_name="us-west-1", 
            aws_access_key_id=access_key, aws_secret_access_key=secret_key)
        table = dynamodb.Table("UpdateStore")
        item = {
            "Id": str(uuid.uuid4()),
            "RepoId": state.state["repo_id"],
            "Timestamp": int(time.time()),
            "ContentType": type,
            "SessionId": state.state["session_id"],
            "Content": repr(message),
        }
        if with_weights:
            item["WeightsS3Key"] = "s3://updatestore/" + weights_s3_key
        table.put_item(Item=item)
    except Exception as e:
        print("DB Error: {0}".format(e))

def add_initial_model():
    """
    Store the initial model in S3. 

    Used for Python libraries, which will load the model directly from here.
    """
    try:
        repo_id = state.state["repo_id"]
        session_id = state.state["session_id"]
        round = 0
        s3 = boto3.resource("s3", aws_access_key_id=access_key, 
            aws_secret_access_key=secret_key)
        model_s3_key = "{0}/{1}/{2}/model.h5"
        model_s3_key = model_s3_key.format(repo_id, session_id, round)
        object = s3.Object("updatestore", model_s3_key)
        h5_filepath = state.state["h5_model_path"]
        object.put(Body=open(h5_filepath, "rb"))
    except Exception as e:
        print("S3 Error: {0}".format(e))

