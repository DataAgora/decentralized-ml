import jwt
import uuid
import warnings

from django.contrib.auth import get_user_model

from calendar import timegm
from datetime import datetime

from rest_framework_jwt.settings import api_settings
from enterprise_users.serializers import UserSerializer

def jwt_response_payload_handler(token, user=None, request=None):
    """ Custom response payload handler.

    This function controlls the custom payload after login or token refresh. This data is returned through the web API.
    """

    # Here you can use other serializers or custom logic, it's up to you!

    return {
        'token': token,
        'user': UserSerializer(user, context={'request': request}).data,
    }


def jwt_payload_handler(user):
    warnings.warn(
        'The following fields will be removed in the future: '
        '`email` and `user_id`. ',
        DeprecationWarning
    )

    payload = {
        'pk': user.pk,
        'username': user.username,
        'exp': datetime.utcnow() + api_settings.JWT_EXPIRATION_DELTA
    }

    if hasattr(user, 'email'):
        payload['email'] = user.email
    if isinstance(user.pk, uuid.UUID):
        payload['pk'] = str(user.pk)

    if hasattr(user, 'first_name'):
        payload['first_name'] = user.first_name
    if hasattr(user, 'last_name'):
        payload['last_name'] = user.last_name
    if hasattr(user, 'enterpriseuserprofile'):
        profile = user.enterpriseuserprofile
        if hasattr(profile, 'company'):
            payload['company'] = profile.company
        if hasattr(profile, 'occupation'):
            payload['occupation'] = profile.occupation

    # Include original issued at time for a brand new token,
    # to allow token refresh
    if api_settings.JWT_ALLOW_REFRESH:
        payload['orig_iat'] = timegm(
            datetime.utcnow().utctimetuple()
        )

    if api_settings.JWT_AUDIENCE is not None:
        payload['aud'] = api_settings.JWT_AUDIENCE

    if api_settings.JWT_ISSUER is not None:
        payload['iss'] = api_settings.JWT_ISSUER

    return payload
