import re
import secrets
import hashlib
import time
import asyncio
from multiprocessing import Process

import boto3
import requests
from flask_cors import CORS
from flask import Flask, request, jsonify

from authorization import _assert_user_can_read_repo, \
    _assert_user_has_repos_left, authorize_user, make_auth_call, \
    _user_can_read_repo
from ecs import create_new_nodes, get_status, stop_nodes, reset_cloud_node, \
    wait_until_next_available_repo, CLOUD_SUBDOMAIN, EXPLORA_SUBDOMAIN, \
    update_cloud_demo_node
from dynamodb import _get_logs, _remove_logs, _get_user_data, \
    _remove_repo_from_user_details, _get_repo_details, _remove_repo_details, \
    _update_user_data_with_new_repo, _create_new_repo_document, \
    _get_all_repos, _get_all_users_repos, _get_demo_api_key, \
    _create_new_repo_document_from_item, DEFAULT_USER_ID
from utils import make_success, make_error, make_unauthorized_error


APPLICATION_NAME = "cloud-node"
app = Flask(__name__)
CORS(app)


@app.route("/")
def home():
    """ 
    Homepage of the API.
    """
    return "This is the dashboard api homepage!"

@app.route('/login', methods=['POST'])
def login():
    """
    Process login request and return results.
    """
    params = request.get_json()
    if "email" not in params:
        return make_error("Missing email from request.")
    if "password" not in params:
        return make_error("Missing password from request.")
    
    try:
        login_details = make_auth_call(params, "login")
    except Exception as e:
        return make_error("Error logging in user: " + str(e))
    
    return make_success(login_details)

@app.route('/registration', methods=['POST'])
def register():
    """
    Process registration request, assign user a demo repo, and start creating
    the next demo repo.
    """
    params = request.get_json()
    if "email" not in params:
        return make_error("Missing email from request.")
    if "password1" not in params:
        return make_error("Missing password from request.")
    if "password2" not in params:
        return make_error("Missing password from request.")
    for arg in ["first_name", "last_name", "company", "occupation"]:
        params[arg] = params.get(arg, "N/A")

    try:
        registration_details = make_auth_call(params, "registration")
        if "token" not in registration_details:
            return make_success(registration_details)
        user_id = registration_details["user"]["pk"]
        repo_id = _assign_user_repo(user_id)
        registration_details["demo_repo_id"] = repo_id
        _create_new_demo_repo(DEFAULT_USER_ID)
        while not _user_can_read_repo(user_id, repo_id):
            time.sleep(0.1)
    except Exception as e:
        return make_error("Error setting up demo node: " + str(e))

    return make_success(registration_details)

@app.route('/reset_state/<repo_id>', methods=['POST'])
def reset_state(repo_id):
    """
    Authorize request, then reset state for cloud node corresponding to given repo_id
    """
    claims = authorize_user(request)
    if claims is None: return make_unauthorized_error()

    user_id = claims["pk"]
    try:
        repo_details = _get_repo_details(user_id, repo_id)
        is_demo = repo_details["IsDemo"]
        reset_cloud_node(repo_id, is_demo)
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
    repo_name = re.sub('[^a-zA-Z0-9-]', '-', repo_name)
    user_id = claims["pk"]
    repo_id, api_key = _create_repo_id_and_api_key()
    try:
        _create_new_repo(user_id, repo_id, api_key, repo_name, \
           repo_description, False)
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
        _delete_repo(user_id, repo_id)
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
        task_arns = [repo_details["CloudTaskArn"], repo_details["ExploraTaskArn"]]
        is_demo = repo_details["IsDemo"]
        status = get_status(task_arns, repo_id, is_demo)
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

def _create_repo_id_and_api_key():
    """
    Creates a new repo ID and API key for a user and repo.
    """
    repo_id = secrets.token_hex(5)
    api_key = secrets.token_hex(5)
    return repo_id, api_key

def _create_new_demo_repo(user_id):
    """
    Helper function to create new demo repo.
    """
    repo_name = "demo-repo-ios"
    repo_description = "Demo repo for training on iOS device."
    repo_id, _ = _create_repo_id_and_api_key()
    api_key = _get_demo_api_key()
    background_process = Process(
        target=_create_new_repo,
        args=(user_id, repo_id, api_key, repo_name, repo_description, True),
        daemon=True
    )
    background_process.start()

def _create_new_repo(user_id, repo_id, api_key, repo_name, repo_description, \
        is_demo):
    """
    Creates a new repo, which includes a cloud and Explora node.
    """
    _assert_user_has_repos_left(user_id)
    server_details = create_new_nodes(repo_id, api_key, is_demo)
    _create_new_repo_document(user_id, repo_id, repo_name, \
        repo_description, server_details, is_demo)
    _update_user_data_with_new_repo(user_id, repo_id)

def _delete_repo(user_id, repo_id):
    """ 
    Helper function to delete repo.
    """
    repo_details = _get_repo_details(user_id, repo_id)
    
    cloud_task_arn = repo_details["CloudTaskArn"]
    cloud_ip_address = repo_details["CloudIpAddress"]
    explora_task_arn = repo_details["ExploraTaskArn"]
    explora_ip_address = repo_details["ExploraIpAddress"]
    is_demo = repo_details["IsDemo"]

    task_arns = [explora_task_arn] \
        if is_demo else [cloud_task_arn, explora_task_arn]
    ip_addresses = [explora_ip_address] \
        if is_demo else [cloud_ip_address, explora_ip_address]
    
    _remove_logs(repo_id)
    _remove_repo_from_user_details(user_id, repo_id)
    _remove_repo_details(user_id, repo_id)

    stop_nodes(task_arns, ip_addresses, repo_id, is_demo)
    
    return repo_details

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

def _assign_user_repo(user_id):
    """
    Helper function to assign user a precreated repo.
    """
    default_repos = _get_all_repos(DEFAULT_USER_ID)
    repo_details = wait_until_next_available_repo(default_repos)
    repo_id = repo_details["Id"]
    repo_details["OwnerId"] = user_id
    _remove_repo_details(DEFAULT_USER_ID, repo_id)
    _remove_repo_from_user_details(DEFAULT_USER_ID, repo_id)
    _create_new_repo_document_from_item(repo_details)        
    _update_user_data_with_new_repo(user_id, repo_id)
    return repo_id

def update_service():
    """
    Update all repos with the latest Docker images for the cloud node and 
    Explora.
    """
    update_cloud_demo_node()

    repos = _get_all_users_repos()
    for user_id, repo_id in repos:
        if repo_id == "cloud-demo":
            continue
        _update_repo(user_id, repo_id)

def precreate_demo_repos(n=5):
    """
    Precreates n demo repos to be assigned when a new user registers.
    """
    for _ in range(n):
        _create_new_demo_repo(DEFAULT_USER_ID)


def _update_repo(user_id, repo_id):
    """
    Helper function to update with the latest Docker images for the cloud node and 
    Explora.
    """
    repo_details = _delete_repo(user_id, repo_id)

    api_key = repo_details["ApiKey"]
    repo_name = repo_details["Name"]
    repo_description = repo_details["Description"]
    is_demo = repo_details["IsDemo"]

    time.sleep(2)
    
    _create_new_repo(user_id, repo_id, api_key, repo_name, repo_description, \
        is_demo)
    

if __name__ == "__main__":
    app.run(port=5001)
