import re
import secrets
import hashlib

import boto3
import requests
from flask_cors import CORS
from flask import Flask, request, jsonify

from authorization import _assert_user_can_read_repo, \
    _assert_user_has_repos_left, authorize_user
from ecs import create_new_nodes, get_status, stop_nodes, CLOUD_SUBDOMAIN, \
    EXPLORA_SUBDOMAIN
from dynamodb import _get_logs, _remove_logs, _get_user_data, \
    _remove_repo_from_user_details, _get_repo_details, _remove_repo_details, \
    _update_user_data_with_new_repo, _create_new_repo_document, _get_all_repos
from utils import make_success, make_error, make_unauthorized_error


APPLICATION_NAME = "cloud-node"
app = Flask(__name__)
CORS(app)


@app.route("/")
def home():
    return "This is the dashboard api homepage!"

@app.route('/reset_state/<repo_id>', methods=['POST'])
def reset_state(repo_id):
    """
    Authorize request, then reset state for cloud node corresponding to given repo_id
    """
    claims = authorize_user(request)
    if claims is None: return make_unauthorized_error()
    try:
        CLOUD_RESET_ENDPOINT = "http://" + CLOUD_SUBDOMAIN + "/secret/reset_state"
        response = requests.get(CLOUD_RESET_ENDPOINT.format(repo_id))
    except Exception as e:
        return make_error("Error resetting state: " + str(e))

    return make_success(repo_id)

@app.route("/userdata", methods=["GET"])
def get_user_data():
    """
    Returns the authenticated user's data.
    """
    # Check authorization
    claims = authorize_user(request)
    if claims is None: return make_unauthorized_error()

    # Get data
    user_id = claims["pk"]
    try:
        user_data = _get_user_data(user_id)
        repos_remaining = user_data['ReposRemaining']
    except Exception as e:
        return make_error("Error getting user data: " + str(e))
    return make_success({"ReposRemaining": True if repos_remaining > 0 else False})

@app.route("/repo/<repo_id>", methods=["GET"])
def get_repo(repo_id):
    """
    Returns a Repo's information (if the user has access to it).
    """
    # Check authorization
    claims = authorize_user(request)
    if claims is None: return make_unauthorized_error()

    # Get data
    user_id = claims["pk"]
    try:
        repo_details = _get_repo_details(user_id, repo_id)
    except Exception as e:
        return make_error("Error while getting the details for this repo: " + str(e))
    return make_success(repo_details)

@app.route("/repo", methods=["POST"])
def create_new_repo():
    """
    Creates a new repo under the authenticated user.

    Example HTTP POST Request body (JSON format):
        {
        	"RepoName": "repo_name",
        	"RepoDescription": "Some description here."
        }
    """
    # Check authorization
    claims = authorize_user(request)
    if claims is None: return make_unauthorized_error()

    # Get parameters
    # TODO: Sanitize inputs.
    params = request.get_json()
    if "RepoName" not in params:
        return make_error("Missing repo name from request.")
    if "RepoDescription" not in params:
        return make_error("Missing repo description from request.")
    repo_name = params["RepoName"][:20]
    repo_description = params["RepoDescription"][:80]

    # TODO: Check repo doesn't already exist.

    user_id = claims["pk"]
    repo_name = re.sub('[^a-zA-Z0-9-]', '-', repo_name)
    try:
        _assert_user_has_repos_left(user_id)
        repo_id, api_key = _create_repo_id_and_api_key(user_id)
        server_details = create_new_nodes(repo_id, api_key)
        _create_new_repo_document(user_id, repo_id, repo_name, \
            repo_description, server_details)
        _update_user_data_with_new_repo(user_id, repo_id, api_key)
    except Exception as e:
        # TODO: Revert things.
        return make_error("Error creating new repo: " + str(e))

    return make_success({"RepoId": repo_id, "ApiKey": api_key})

@app.route("/delete/<repo_id>", methods=["POST"])
def delete_repo(repo_id):
    """
    Deletes a repo under the authenticated user.
    """
    # Check authorization
    claims = authorize_user(request)
    if not claims: return make_unauthorized_error()

    user_id = claims["pk"]
    try:
        repo_details = _get_repo_details(user_id, repo_id)
        cloud_task_arn = repo_details["CloudTaskArn"]
        cloud_ip_address = repo_details["CloudIpAddress"]
        explora_task_arn = repo_details["ExploraTaskArn"]
        explora_ip_address = repo_details["ExploraIpAddress"]
        _remove_logs(repo_id)
        _remove_repo_from_user_details(user_id, repo_id)
        _remove_repo_details(user_id, repo_id)
        stop_nodes(cloud_task_arn, explora_task_arn, repo_id, cloud_ip_address, explora_ip_address)
    except Exception as e:
        # TODO: Revert things.
        return make_error("Error deleting repo: " + str(e))

    return make_success(repo_id)

@app.route("/repos", methods=["GET"])
def get_all_repos():
    """
    Returns all repos the user has access to.
    """
    # Check authorization
    claims = authorize_user(request)
    if claims is None: return make_unauthorized_error()

    # Get data
    user_id = claims["pk"]
    try:
        repo_list = _get_all_repos(user_id)
    except Exception as e:
        return make_error("Error while getting list of repos: " + str(e))
    return make_success(repo_list)

@app.route("/logs/<repo_id>", methods=["GET"])
def get_logs(repo_id):
    """
    Returns all logs for a Repo the user has access to.
    """
    # Check authorization
    claims = authorize_user(request)
    if claims is None: return make_unauthorized_error()

    # Get data
    user_id = claims["pk"]
    try:
        _assert_user_can_read_repo(user_id, repo_id)
        logs = _get_logs(repo_id)
    except Exception as e:
        return make_error("Error getting logs: " + str(e))
    return make_success(logs)

@app.route("/coordinator/status/<repo_id>", methods=["GET"])
def get_task_status(repo_id):
    """
    Returns the status of the Cloud Node associated to a Repo the user has
    access to.
    """
    # Check authorization
    claims = authorize_user(request)
    if claims is None: return make_unauthorized_error()

    # Get data
    user_id = claims["pk"]
    try:
        repo_details = _get_repo_details(user_id, repo_id)
        cloud_task_arn = repo_details["CloudTaskArn"]
        explora_task_arn = repo_details["ExploraTaskArn"]
        status = get_status(cloud_task_arn, explora_task_arn, repo_id)
    except Exception as e:
        return make_error("Error checking status: " + str(e))
    return make_success(status)

@app.route("/model", methods=["POST"])
def download_model():
    """
    Returns the download url of a model.

    Example HTTP POST Request body (JSON format):
        {
          "RepoId": "test",
          "SessionId": "c257efa4-791d-4130-bdc6-b0d3cee5fa25",
          "Round": 5
        }
    """
    # Check authorization
    claims = authorize_user(request)
    if claims is None: return make_unauthorized_error()

    # Get parameters
    params = request.get_json()
    if "RepoId" not in params:
        return make_error("Missing repo id from request.")
    if "SessionId" not in params:
        return make_error("Missing session id from request.")
    if "Round" not in params:
        return make_error("Missing round from request.")
    repo_id  = params.get('RepoId', None)
    session_id  = params.get('SessionId', None)
    round  = params.get('Round', None)
    bucket_name = "updatestore"
    object_name = "{0}/{1}/{2}/model.h5".format(repo_id, session_id, round)

    # Get presigned URL
    user_id = claims["pk"]
    try:
        _assert_user_can_read_repo(user_id, repo_id)
        url = _create_presigned_url(bucket_name, object_name)
    except Exception as e:
        return make_error("Error getting download URL: " + str(e))

    # Return url
    return make_success(url)

def _create_repo_id_and_api_key(user_id):
    """
    Creates a new repo ID and API key for a user and repo.
    """
    repo_id = secrets.token_hex(16)
    true_api_key = secrets.token_urlsafe(32)
    h = hashlib.sha256()
    h.update(true_api_key.encode('utf-8'))
    api_key = h.hexdigest()
    return repo_id, api_key

def _create_new_cloud_node(repo_id, api_key):
    """
    Creates a new cloud node.
    """
    try:
        run_new_task(repo_id)
    except Exception as e:
        raise Exception("Error while creating new cloud node: " + str(e))

def _create_presigned_url(bucket_name, object_name, expiration=3600):
    """Generate a presigned URL to share an S3 object

    :param bucket_name: string
    :param object_name: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """

    # Generate a presigned URL for the S3 object
    s3_client = boto3.client('s3')
    try:
        response = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': bucket_name,
                'Key': object_name
            },
            ExpiresIn=expiration
        )
    except ClientError as e:
        raise Exception("Error while creating S3 presigned url.")

    # The response contains the presigned URL
    return response

if __name__ == "__main__":
    app.run(port=5001)
