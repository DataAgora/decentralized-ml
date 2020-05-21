import jwt
import json
import requests

from dynamodb import _get_user_data


AUTH_ENDPOINT = "https://eauth.discreetai.com/auth/{}/"


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
        can_read_repos = _user_can_read_repo(user_id, repo_id)
    except:
        raise Exception("Error while getting user's permissions.")
    assert can_read_repos, "You don't have permissions for this repo."

def _user_can_read_repo(user_id, repo_id):
    """
    Helper function to get determine whether the user can read a particular
    repo.
    """
    user_data = _get_user_data(user_id)
    repos_managed = user_data['ReposManaged']
    return repo_id in repos_managed

def authorize_user(request):
    """
    Helper function that authorizes a request/user based on the JWT Token
    provided. Return the claims if successful, `None` otherwise.
    """
    try:
        jwt_string = request.headers.get("Authorization").split('Bearer ')[1]
        with open("jwt.json", "r") as f:
            jwt_json = json.load(f)
            JWT_SECRET = jwt_json["JWT_SECRET"]
            JWT_ALGO = jwt_json["JWT_ALGO"]
            claims = jwt.decode(jwt_string, JWT_SECRET, algorithms=[JWT_ALGO])
    except Exception as e:
        return None
    
    return claims

def make_auth_call(data, action):
    """
    Make call to auth server with the provided action.

    Args:
        data (dict): The data to send.
        action (str): The endpoint to call on the auth server. Must be 
            `login` or `registration`.

    Returns:
        dict: The response from the auth server.
    """
    endpoint = AUTH_ENDPOINT.format(action)
    headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
    response = requests.post(endpoint, headers=headers, data=json.dumps(data))
    return response.json()
