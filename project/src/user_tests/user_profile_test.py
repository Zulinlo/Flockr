"""
user_profile_test.py

Fixtures:
    register_login: creates a user and logs into that user

Test Modules:
    test_valid_user: success case for when user_profile is successfully returned
    test_invalid_uid: fail case for invalid user id being passed in
    test_invalid_token: fail case for invalid token being passed in
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import pytest
from implement.other          import clear
from error          import InputError, AccessError
from implement.auth           import auth_register, auth_login
from implement.user           import user_profile
from helper         import token_hash

@pytest.fixture
def register_login():
    # Fixture registers a user and then logs them in
    # Returns dictionary containing their u_id and token.
    clear()

    # Create dummy user to make sure right user is being targetted
    auth_register("ignoreme@gmail.com", "password", "Bungus", "Boe")

    auth_register("test@gmail.com", "password", "Angus", "Doe")
    user = auth_login("test@gmail.com", "password")

    return user

def test_valid_user(register_login):
    # Setting up valid token and u_id to be passed into user_profile.
    user = register_login
    token = user["token"]
    u_id = user["u_id"]
    result = user_profile(token, u_id)
    # Since all inputs are valid, should return the users data. 
    assert result == {
        'user': {
        	'u_id': 1,
        	'email': 'test@gmail.com',
        	'name_first': 'Angus',
        	'name_last': 'Doe',
        	'handle_str': 'angusdoe',
                'permission_id': 2,
                'profile_img_url': 'default.jpg'
        },
    }

def test_invalid_uid(register_login):
    # Setting up invalid u_id to be passed into user_profile.
    user = register_login
    token = user["token"]
    u_id = 'invalid_uid'
    # u_id is invalid since u_id can only have numerical values.
    # Since u_id is invalid, function should raise an InputError.
    with pytest.raises(InputError):
        user_profile(token, u_id)

def test_invalid_token(register_login):
    # Setting up invalid token to be passed into user_profile.
    user = register_login
    u_id = user["u_id"]
    # token is invalid since token can only have numerical values.
    # Since token is invalid, function should raise an InputError.
    with pytest.raises(AccessError):
        user_profile(token_hash(2), u_id)
