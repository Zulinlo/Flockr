import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

from data   import data
from error  import AccessError, InputError
import jwt
import hashlib

SECRET = 'shenpai'


def token_validator(encoded_jwt):
    """
    token_validator

    Returns:
        the user's info if token is valid

    Raises:
        AccessError when no user is found given the token
    """

    encoded_jwt = encoded_jwt.encode('utf-8')
    decoded_jwt = jwt.decode(encoded_jwt, SECRET, algorithms=['HS256'])
    
    # Checks if payload user details exists
    for user in data['users']:
        if decoded_jwt['u_id'] == user['u_id']:
            return decoded_jwt

    raise AccessError("Invalid token")


def token_hash(u_id):
    """
    token_hash

    Returns:
        a hashed jwt token
    """

    encoded_jwt = jwt.encode({"u_id": u_id}, SECRET, algorithm = 'HS256')
    # Decoded hashed token so it returns a string 
    return encoded_jwt.decode('utf-8')


def u_id_validator(u_id):
    """
    u_id_validator

    Args:
        u_id: validates user_id as a user of the flockr
    
    Returns:
        The u_id which has been passed in
    
    Raises:
        InputError when the users id has not been found in the data
    """

    for user in data['users']:
        if u_id == user['u_id']:
            return u_id

    raise InputError("Invalid User ID.")


def is_flockr_owner(token, u_id):
    """
    is_flockr_owner

    Returns:
        True if the user is a Flockr owner
        False if the user is not a Flockr owner
    """

    is_flockr_owner = None

    for user in data['users']:
        if user['u_id'] == u_id:
            is_flockr_owner = user['permission_id']

    return is_flockr_owner == 1


def password_hash(password):
    """
    password_hash

    Returns:
        A hashed password
    """

    encoded_password = hashlib.sha256(password.encode()).hexdigest()

    return encoded_password


def channel_validator(channel_id):
    """
    channel_validator

    Returns:
        the channel_id if it is valid

    Raises:
        InputError when no channel in data has corresponding channel_id
    """

    for channel in data['channels']:
        if channel_id == channel['channel_id']:
            return channel_id

    raise InputError("Channel ID is not a valid channel.")
