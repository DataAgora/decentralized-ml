import re
import time
import secrets
import decimal
import hashlib

import jwt
import boto3
import requests
from flask_cors import CORS
from boto3.dynamodb.conditions import Key, Attr
from flask import Flask, request, jsonify

from deploy import create_new_nodes, stop_nodes, CLOUD_SUBDOMAIN, \
    EXPLORA_SUBDOMAIN
from dynamodb import DB


JWT_SECRET = "datajbsnmd5h84rbewvzx6*cax^jgmqw@m3$ds_%z-4*qy0n44fjr5shark"
JWT_ALGO = "HS256"

APPLICATION_NAME = "cloud-node"
app = Flask(__name__)
CORS(app)
CLOUD_BASE_ENDPOINT = "http://{CLOUD_SUBDOMAIN}/secret/reset_state"

@app.route("/")
def home():
    return "This is the dashboard api homepage!"

@app.route('/reset_state/<repo_id>', methods=['POST', 'GET'])
def reset_state(repo_id):
    """
    Authorize request, then reset state for cloud node corresponding to given repo_id
    """
    claims = authorize_user(request, use_header=False)
    if claims is None: return jsonify(make_unauthorized_error()), 200
    try:
        response = requests.get(CLOUD_BASE_ENDPOINT.format(repo_id))
    except Exception as e:
        print("Error: " + str(e))
        return jsonify(make_error(str(e)))

    return jsonify(make_success(response.text))

@app.route('/get_username/<repo_id>', methods=['POST', 'GET'])
def get_username(repo_id):
    """
    Authorize request, then retrieve username for given repo_id
    """
    claims = authorize_user(request, use_header=False)
    if claims is None: return jsonify(make_unauthorized_error()), 200
    user_id = claims["pk"]
    try:
        users_table = _get_dynamodb_table("jupyterhub-users")
        repos_table = _get_dynamodb_table("Repos")
        db = DB(users_table, repos_table)
        username = db.get_username(user_id, repo_id)
    except Exception as e:
        print("Error: " + str(e))
        return jsonify(make_error(str(e)))

    return jsonify(make_success(username))

@app.route("/userdata", methods=["GET"])
def get_user_data():
    """
    Returns the authenticated user's data.
    """
    # Check authorization
    claims = authorize_user(request)
    if claims is None: return jsonify(make_unauthorized_error()), 200

    # Get data
    user_id = claims["pk"]
    try:
        user_data = _get_user_data(user_id)
        repos_remaining = user_data['ReposRemaining']
    except:
        return jsonify(make_error("Error while getting user's permissions.")), 200
    return jsonify({"ReposRemaining": True if repos_remaining > 0 else False})

@app.route("/repo/<repo_id>", methods=["GET"])
def get_repo(repo_id):
    """
    Returns a Repo's information (if the user has access to it).
    """
    # Check authorization
    claims = authorize_user(request)
    if claims is None: return jsonify(make_unauthorized_error()), 200

    # Get data
    user_id = claims["pk"]
    try:
        repo_details = _get_repo_details(user_id, repo_id)
    except:
        return jsonify(make_error("Error while getting the details for this repo.")), 200
    return jsonify(repo_details)

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
    if claims is None: return jsonify(make_unauthorized_error()), 200

    # Get parameters
    # TODO: Sanitize inputs.
    params = request.get_json()
    if "RepoName" not in params:
        return jsonify(make_error("Missing repo name from request.")), 200
    if "RepoDescription" not in params:
        return jsonify(make_error("Missing repo description from request.")), 200
    repo_name = params["RepoName"][:20]
    repo_description = params["RepoDescription"][:80]

    # TODO: Check repo doesn't already exist.

    user_id = claims["pk"]
    repo_name = re.sub('[^a-zA-Z0-9-]', '-', repo_name)
    try:
        _assert_user_has_repos_left(user_id)
        repo_id = secrets.token_hex(16)
        server_details = create_new_nodes(repo_id)
        _create_new_repo_document(user_id, repo_id, repo_name, \
            repo_description, server_details)
        api_key, true_api_key = _create_new_api_key(user_id, repo_id)
        _update_user_data_with_new_repo(user_id, repo_id, api_key)
    except Exception as e:
        # TODO: Revert things.
        return jsonify(make_error(str(e))), 200

    return jsonify({
        "Error": False,
        "Results": {
            "RepoId": repo_id,
            "TrueApiKey": true_api_key
        }
    })

@app.route("/delete/<repo_id>", methods=["POST"])
def delete_repo(repo_id):
    """
    Deletes a repo under the authenticated user.
    """
    # Check authorization
    claims = authorize_user(request, use_header=False)
    if not claims: return jsonify(make_unauthorized_error()), 200

    user_id = claims["pk"]
    try:
        api_key = _remove_api_key(user_id, repo_id)
        repo_details = _get_repo_details(user_id, repo_id)
        cloud_task_arn = repo_details["CloudTaskArn"]
        cloud_ip_address = repo_details["CloudIpAddress"]
        _remove_logs(repo_id)
        _remove_repo_from_user_details(user_id, repo_id, api_key)
        _remove_creds_from_repo(user_id, repo_id)
        _remove_repo_details(user_id, repo_id)
        stop_nodes(cloud_task_arn, repo_id, cloud_ip_address)
    except Exception as e:
        # TODO: Revert things.
        return jsonify(make_error(str(e))), 200

    return jsonify({
        "Error": False,
    })

@app.route("/repos", methods=["GET"])
def get_all_repos():
    """
    Returns all repos the user has access to.
    """
    # Check authorization
    claims = authorize_user(request)
    if claims is None: return jsonify(make_unauthorized_error()), 200

    # Get data
    user_id = claims["pk"]
    try:
        repo_list = _get_all_repos(user_id)
    except:
        return jsonify(make_error("Error while getting list of repos.")), 200
    return jsonify(repo_list)

@app.route("/logs/<repo_id>", methods=["GET"])
def get_logs(repo_id):
    """
    Returns all logs for a Repo the user has access to.
    """
    # Check authorization
    claims = authorize_user(request)
    if claims is None: return jsonify(make_unauthorized_error()), 200

    # Get data
    user_id = claims["pk"]
    try:
        _assert_user_can_read_repo(user_id, repo_id)
        logs = _get_logs(repo_id)
    except Exception as e:
        return jsonify(make_error(str(e)))
    return jsonify(logs)

@app.route("/coordinator/status/<repo_id>", methods=["GET"])
def get_coordinator_status(repo_id):
    """
    Returns the status of the Cloud Node associated to a Repo the user has
    access to.
    """
    # Check authorization
    claims = authorize_user(request)
    if claims is None: return jsonify(make_unauthorized_error()), 200

    # Get data
    user_id = claims["pk"]
    try:
        cloud_node_url = CLOUD_SUBDOMAIN.format(repo_id)
        # TODO: Add HTTPS to cloud node
        r = requests.get("http://" + cloud_node_url + "/status")
        status_data = r.json()
        assert "Busy" in status_data
    except Exception as e:
        return jsonify(make_error("Error while checking coordinator's status.")), 200
    return jsonify(status_data)

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
    if claims is None: return jsonify(make_unauthorized_error()), 200

    # Get parameters
    params = request.get_json()
    if "RepoId" not in params:
        return jsonify(make_error("Missing repo id from request.")), 200
    if "SessionId" not in params:
        return jsonify(make_error("Missing session id from request.")), 200
    if "Round" not in params:
        return jsonify(make_error("Missing round from request.")), 200
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
        return jsonify(make_error(str(e))), 200

    # Return url
    return jsonify({'DownloadUrl': url})

def _assert_user_has_repos_left(user_id):
    """
    Asserts that the user has any repos available to create.
    """
    user_data = _get_user_data(user_id)
    assert int(user_data['ReposRemaining']) > 0, "You don't have any repos left."

def _assert_user_can_read_repo(user_id, repo_id):
    """
    Asserts the user can read a particular repo.
    """
    try:
        user_data = _get_user_data(user_id)
        repos_managed = user_data['ReposManaged']
    except:
        raise Exception("Error while getting user's permissions.")
    assert repo_id in repos_managed, "You don't have permissions for this repo."

def _get_logs(repo_id):
    """
    Returns the logs for a repo.
    """
    logs_table = _get_dynamodb_table("UpdateStore")
    try:
        response = logs_table.query(
            KeyConditionExpression=Key('RepoId').eq(repo_id) \
                & Key('ExpirationTime').gt(int(time.time())) 
        )
        logs = response["Items"]
    except Exception as e:
        raise Exception("Error while getting logs for repo. " + str(e))
    return logs

def _remove_logs(repo_id):
    """
    Removes the logs for a repo.
    """
    logs_table = _get_dynamodb_table("UpdateStore")
    try:
        response = logs_table.query(
            KeyConditionExpression=Key('RepoId').eq(repo_id)
        )
        with logs_table.batch_writer() as batch:
            for item in response["Items"]:
                batch.delete_item(
                    Key={
                        'RepoId': item['RepoId'],
                        'Timestamp': item['Timestamp']
                    }
                )
        print("Successfully deleted logs!")
        return True
    except Exception as e:
        raise Exception("Error while getting logs for repo. " + str(e))

def _get_user_data(user_id):
    """
    Returns the user's data.
    """
    table = _get_dynamodb_table("UsersDashboardData")
    try:
        response = table.get_item(
            Key={
                "UserId": user_id,
            }
        )
        data = response["Item"]
    except:
        raise Exception("Error while getting user dashboard data.")
    return data

def _remove_repo_from_user_details(user_id, repo_id, api_key):
    """
    Upon removing a repo, remove the repo from the user's details.
    """
    table = _get_dynamodb_table("UsersDashboardData")
    try:
        response = table.get_item(
            Key={
                "UserId": user_id,
            }
        )
        data = response["Item"]
        repos_managed = data['ReposManaged']
        api_keys = data['ApiKeys']
        if repo_id in repos_managed and api_key in api_keys:
            repos_managed.remove(repo_id)
            api_keys.remove(api_key)
            if len(repos_managed) == 0:
                data.pop('ReposManaged')
                data.pop('ApiKeys')
            data['ReposRemaining'] += 1
            table.put_item(
                Item=data
            )
            print("Successfully removed repo_id from user details!")
            return True
        else:
            raise Exception("Could not find corresponding API key or repo id!")
    except Exception as e:
        raise Exception("Error while removing user dashboard data: " + str(e))


def _get_repo_details(user_id, repo_id):
    """
    Returns a repo's details.
    """
    repos_table = _get_dynamodb_table("Repos")
    try:
        response = repos_table.get_item(
            Key={
                "Id": repo_id,
                "OwnerId": user_id,
            }
        )
        repo_details = response["Item"]
    except:
        raise Exception("Error while getting repo details.")
    return repo_details

def _remove_repo_details(user_id, repo_id):
    """
    Removes a repo's details.
    """
    repos_table = _get_dynamodb_table("Repos")
    try:
        response = repos_table.delete_item(
            Key={
                "Id": repo_id,
                "OwnerId": user_id,
            }
        )
        print("Removed repo details!")
        return True
    except:
        raise Exception("Error while getting repo details.")

def _remove_creds_from_repo(user_id, repo_id):
    repos_table = _get_dynamodb_table("Repos")
    users_table = _get_dynamodb_table('jupyterhub-users')
    try:
        response = repos_table.get_item(
            Key={
                "Id": repo_id,
                "OwnerId": user_id,
            }
        )
        repo_details = response["Item"]
        username = repo_details['creds']
        repos_table.update_item(
            Key={
                "Id": repo_id,
                "OwnerId": user_id,
            },
            UpdateExpression='SET creds = :val1',
            ExpressionAttributeValues={
                ':val1': 'N/A',
            }
        )
        users_table.update_item(
            Key = {
                'username': username
            },
            UpdateExpression='SET in_use = :val1',
            ExpressionAttributeValues={
                ':val1': False
            }
        )
    except:
        raise Exception("Error while removing repo creds.")


def _update_user_data_with_new_repo(user_id, repo_id, api_key):
    """
    Updates a user with a new repo and its metadata.
    """
    table = _get_dynamodb_table("UsersDashboardData")
    try:
        response = table.get_item(
            Key={
                "UserId": user_id,
            }
        )
        data = response["Item"]

        repos_managed = data.get('ReposManaged', set([]))
        api_keys = data.get('ApiKeys', set([]))

        repos_managed.add(repo_id)
        api_keys.add(api_key)

        response = table.update_item(
            Key={
                'UserId': user_id,
            },
            UpdateExpression="SET ReposRemaining = ReposRemaining - :val, ReposManaged = :val2, ApiKeys = :val3",
            ExpressionAttributeValues={
                ':val': decimal.Decimal(1),
                ':val2': repos_managed,
                ':val3': api_keys,
            }
        )
    except Exception as e:
        raise Exception("Error while updating user data with new repo data: " + str(e))

def _create_new_repo_document(user_id, repo_id, repo_name, repo_description, \
        server_details):
    """
    Creates a new repo document in the DB.
    """
    table = _get_dynamodb_table("Repos")
    try:
        item = {
            'Id': repo_id,
            'Name': repo_name,
            'Description': repo_description,
            'OwnerId': user_id,
            'ContributorsId': [],
            'CoordinatorAddress': CLOUD_SUBDOMAIN.format(repo_id),
            'CreatedAt': int(time.time()),
            'creds': 'N/A'
        }
        item.update(server_details)
        table.put_item(Item=item)
    except:
        raise Exception("Error while creating the new repo document.")
    return repo_id

def _create_new_api_key(user_id, repo_id):
    """
    Creates a new API Key for an user and repo.
    """
    table = _get_dynamodb_table("ApiKeys")
    true_api_key = secrets.token_urlsafe(32)
    h = hashlib.sha256()
    h.update(true_api_key.encode('utf-8'))
    api_key = h.hexdigest()
    try:
        item = {
            'Key': api_key,
            'OwnerId': user_id,
            'RepoId': repo_id,
            'CreatedAt': int(time.time()),
        }
        table.put_item(Item=item)
    except:
        raise Exception("Error while creating a new API key.")
    return api_key, true_api_key

def _remove_api_key(user_id, repo_id):
    table = _get_dynamodb_table("ApiKeys")
    try:
        response = table.scan(
            FilterExpression=Attr('RepoId').eq(repo_id)
        )
        items = response['Items']
        assert len(items) > 0, "Should have found repo in API keys table!"
        item = items[0]
        api_key = item['Key']
        table.delete_item(
            Key={
                'Key': item['Key'],
                'OwnerId': item['OwnerId']
            }
        )
        return api_key
    except:
        raise Exception("Error while deleting API key.")
    

def _get_all_repos(user_id):
    """
    Returns all repos for a user.
    """
    try:
        user_data = _get_user_data(user_id)
        repos_managed = user_data.get('ReposManaged', 'None')

        repos_table = _get_dynamodb_table("Repos")
        all_repos = []
        for repo_id in repos_managed:
            if repo_id == "null": continue
            response = repos_table.get_item(
                Key={
                    "Id": repo_id,
                    "OwnerId": user_id,
                }
            )

            if 'Item' in response:
                all_repos.append(response['Item'])
    except:
        raise Exception("Error while getting all repos.")
    return all_repos

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

def _get_dynamodb_table(table_name):
    """
    Helper function that returns an AWS DynamoDB table object.
    """
    dynamodb = boto3.resource('dynamodb', region_name='us-west-1')
    table = dynamodb.Table(table_name)
    return table

def authorize_user(request, use_header=True):
    """
    Helper function that authorizes a request/user based on the JWT Token
    provided. Return the claims if successful, `None` otherwise.
    """
    try:
        if use_header:
            jwt_string = request.headers.get("Authorization").split('Bearer ')[1]
        else:
            jwt_string = request.get_json().get("token")
        claims = jwt.decode(jwt_string, JWT_SECRET, algorithms=[JWT_ALGO])
    except Exception as e:
        return None
    
    return claims

def make_unauthorized_error():
    """
    Helper function that returns an unauthorization error.
    """
    return make_error('Authorization failed.')

def make_error(msg):
    """
    Helper function to create an error message to return on failed requests.
    """
    return {'Error': True, 'Message': msg}

def make_success(msg):
    """
    Helper function to create a success message to return on successful
    requests.
    """
    return {'Error': False, 'Message': msg}


if __name__ == "__main__":
    app.run(port=5001)
