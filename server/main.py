from flask import Flask, request, jsonify
import os
import jwt
from flask_cors import CORS, cross_origin

from dynamodb import DB


application = Flask(__name__)
db = DB()
CORS(application, headers=['Content-Type', 'Authorization'], supports_credentials=True, 
        expose_headers='Authorization', origins='*')

JWT_SECRET = "datajbsnmd5h84rbewvzx6*cax^jgmqw@m3$ds_%z-4*qy0n44fjr5shark"
JWT_ALGO = "HS256"

@application.route('/')
def landing():
    return "This is the homepage of the Explora server!!!!"

@application.route('/get_username/<repo_id>', methods=['POST', 'GET'])
def get_username(repo_id):
    '''
    Authorize request, then retrieve username for given repo_id
    '''
    claims = authorize_user(request)
    if claims is None: return jsonify(make_unauthorized_error()), 400
    user_id = claims["pk"]
    try:
        username = db.get_username(user_id, repo_id)
    except Exception as e:
        return jsonify(make_error(str(e)))

    return jsonify(make_success(username))

def authorize_user(request):
    """
    Helper function that authorizes a request/user based on the JWT Token
    provided. Return the claims if successful, `None` otherwise.
    """
    try:
        jwt_string = request.get_json().get("token")
        claims = jwt.decode(jwt_string, JWT_SECRET, algorithms=[JWT_ALGO])
    except Exception as e:
        print(str(e))
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
    return {'success': False, 'message': msg}

def make_success(msg):
    """
    Helper function to create a success message to return on successful requests.
    """
    return {'success': True, 'message': msg}

if __name__ == '__main__':
    from twisted.python import log
    log.startLogging(sys.stdout)
    application.run(host="0.0.0.0")