import os

import boto3
from boto3.dynamodb.conditions import Key, Attr

from utils.enums import ErrorMessages


CLOUD_SUBDOMAIN = "ws://{}.cloud.discreetai.com"

def upload_keras_model(repo_id, session_id, model_path, is_mlmodel):
    """
    Upload the Keras model to S3 at the beginning of the session.

    Args:
        repo_id (str): The repo ID associated with the current application.
        session_id (str): The session ID that uniquely identifies this
            session.
        model_path (str): The filepath to the saved model.
        is_mlmodel (bool): Boolean for whether the specified model is an
            MLModel or not.
    """
    try:
        s3 = boto3.resource("s3")
        model_s3_key = "{0}/{1}/{2}/{3}"
        model_name = "my_model.mlmodel" if is_mlmodel else "model.h5"
        model_s3_key = model_s3_key.format(repo_id, session_id, 0, model_name)
        object = s3.Object("updatestore", model_s3_key)
        object.put(Body=open(model_path, "rb"))
        return True
    except Exception as e:
        print("S3 Error: {0}".format(e))
        return False

def _get_repo_details(repo_id):
    """
    Helper function to get repo details from DynamoDB.

    Args:
        repo_id (str): The repo ID associated with the current application.

    Returns:
        dict: The repo details, if the DynamoDB operation succeeded.
    """
    try:
        dynamodb = boto3.resource('dynamodb', region_name='us-west-1')
        table = dynamodb.Table("Repos")
        response = table.query(
            KeyConditionExpression=Key('Id').eq(repo_id)
        )

        if not response["Items"]:
            print("An error occurred during setup.")
            return

        return response["Items"][0]
    except Exception as e:
        print("DynamoDB error: {}".format(e))
        
def get_websocket_url(repo_id):
    """
    If the repo ID is valid, retrieve the websocket URL of the server.

    Args:
        repo_id (str): The repo ID associated with the current application.

    Returns:
        str: The URL of the server, if the repo ID is valid.
    """
    repo_details = _get_repo_details(repo_id)

    if not repo_details:
        return

    if repo_details["IsDemo"]:
        repo_id = _get_repo_details("cloud-demo")["CloudDomain"]

    return CLOUD_SUBDOMAIN.format(repo_id)
        