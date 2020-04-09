import jwt

from dynamodb import _get_user_data


JWT_SECRET = "datajbsnmd5h84rbewvzx6*cax^jgmqw@m3$ds_%z-4*qy0n44fjr5shark"
JWT_ALGO = "HS256"

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

def authorize_user(request):
    """
    Helper function that authorizes a request/user based on the JWT Token
    provided. Return the claims if successful, `None` otherwise.
    """
    try:
        jwt_string = request.get_json().get("token")
        claims = jwt.decode(jwt_string, JWT_SECRET, algorithms=[JWT_ALGO])
    except Exception as e:
        return None
    
    return claims
    