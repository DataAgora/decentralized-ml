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
    