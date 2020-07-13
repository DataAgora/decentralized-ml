import jwt
import json
import requests

from dynamodb import _get_user_data


AUTH_ENDPOINT = "https://eauth.discreetai.com/auth/{}/"


def set_up_secret_key(app):
    with open("jwt.json", "r") as f:
        app.config["SECRET_KEY"] = json.load(f).get("JWT_SECRET")

def _assert_user_has_repos_left(username):
    """
    Asserts that the user has any repos available to create.
    """
    user_data = _get_user_data(username)
    assert int(user_data['ReposRemaining']) > 0, "You don't have any repos left."

def _assert_user_can_read_repo(username, repo_id):
    """
    Asserts the user can read a particular repo.
    """
    try:
        can_read_repos = _user_can_read_repo(username, repo_id)
    except:
        raise Exception("Error while getting user's permissions.")
    assert can_read_repos, "You don't have permissions for this repo."

def _user_can_read_repo(username, repo_id):
    """
    Helper function to get determine whether the user can read a particular
    repo.
    """
    user_data = _get_user_data(username)
    repos_managed = user_data['ReposManaged']
    return repo_id in repos_managed

class User(object):
    def __init__(self, data):
        self.id = data["Username"]
        self.username = data["Username"]
        self.data = data

    def __str__(self):
        return "User(id='%s')" % self.id

def authenticate(username, password):
    try:
        data = _get_user_data(username)
        if password == data["Password"]:
            return User(data)
    except Exception as e:
        raise e
        print("Failed to authorize {}".format(username))

def identity(payload):
    username = payload['identity']
    data = _get_user_data(username)
    return User(data)
    