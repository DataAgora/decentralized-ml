import boto3


def upload_keras_model(repo_id, session_id, h5_model_path):
    """
    Upload the Keras model to S3 at the beginning of the session.

    Args:
        repo_id (str): The repo ID associated with the current dataset.
        session_id (str): The session ID that uniquely identifies this
            session.
        h5_model_path (str): The filepath to the saved Keras model.
    """
    try:
        s3 = boto3.resource("s3")
        model_s3_key = "{0}/{1}/{2}/model.h5"
        model_s3_key = model_s3_key.format(repo_id, session_id, 0)
        object = s3.Object("updatestore", model_s3_key)
        object.put(Body=open(h5_model_path, "rb"))
        return True
    except Exception as e:
        print("S3 Error: {0}".format(e))
        return False