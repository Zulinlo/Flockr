'''
user_profile_sethandle_test.py

Fixtures:
    register_login: registers a user and logs that user in

Test Modules:
    test_valid_handle_str: tests valid handle where no errors should be raised
    test_same_handle: tests when new handle is already in use
    test_invalid_short3: tests when new handle is exactly 3 characters long
    test_invalid_short: tests when new handle is less than 3 characters long
    test_invalid_long20: tests when new handle is exaclty 20 characters long
    test_invalid_long: tests when new handle is more than 20 characters long
'''
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import pytest
from implement.auth           import auth_register, auth_login
from implement.user           import user_profile, user_profile_sethandle
from error          import InputError
from implement.other          import clear
from helper         import token_hash

@pytest.fixture
def register_login():
    # Fixture registers a user and then logs them in
    # Returns dictionary containing their u_id and token.
    clear()
    
    # Create dummy user to make sure right user is being targetted
    auth_register("ignoreme@gmail.com", "password", "Anguss", "Doee")

    auth_register("test@gmail.com", "password", "Angus", "Doe")
    user = auth_login("test@gmail.com", "password")
    return user

def test_valid_handle_str(register_login):
    # Setting up valid token to be passed into user_profile_sethandle.
    user = register_login
    token = user["token"]
    u_id = user["u_id"]
    profile = user_profile(token, u_id)['user']

    # Current handle should be default concatenation of first and last name.
    current_handle = profile['handle_str']
    assert current_handle == 'angusdoe'

    # handle_str will be valid since unique and between 3 & 20 characters.
    handle_str = 'test_new_handle'
    user_profile_sethandle(token, handle_str)

    # Since all inputs are valid, the users handle should be updated as 
    # 'test_new_handle'
    new_handle = user_profile(token, u_id)['user']['handle_str']
    assert new_handle == handle_str

def test_same_handle(register_login):
    # Setting up valid token to be passed into user_profile_sethandle.
    user = register_login
    token = user["token"]
    u_id = user["u_id"]
    profile = user_profile(token, u_id)['user']
    # Current handle should be default concatenation of first and last name.
    current_handle = profile['handle_str']
    assert current_handle == 'angusdoe'
    # handle_str will be invalid as current user already using that handle 
    handle_str = 'angusdoe'
    # Since handle_str is already used, it should raise an input error
    with pytest.raises(InputError):
        user_profile_sethandle(token, handle_str)

def test_invalid_short3(register_login):
    # Setting up valid token to be passed into user_profile_sethandle.
    user = register_login
    token = user["token"]
    u_id = user["u_id"]
    profile = user_profile(token, u_id)['user']
    # Current handle should be default concatenation of first and last name.
    current_handle = profile['handle_str']
    assert current_handle == 'angusdoe'
    # handle_str will be invalid as it is 3 characters
    handle_str = 'xdd'
    # Since handle_str is too short, it should raise an input error
    with pytest.raises(InputError):
        user_profile_sethandle(token, handle_str)

def test_invalid_short(register_login):
  # Setting up valid token to be passed into user_profile_sethandle.
    user = register_login
    token = user["token"]
    u_id = user["u_id"]
    profile = user_profile(token, u_id)['user']
    # Current handle should be default concatenation of first and last name.
    current_handle = profile['handle_str']
    assert current_handle == 'angusdoe'
    # handle_str will be invalid as it is less than 3 characters
    handle_str = 'xd'
    # Since handle_str is too short, it should raise an input error
    with pytest.raises(InputError):
        user_profile_sethandle(token, handle_str)

def test_invalid_long20(register_login):
    # Setting up valid token to be passed into user_profile_sethandle.
    user = register_login
    token = user["token"]
    u_id = user["u_id"]
    profile = user_profile(token, u_id)['user']
    # Current handle should be default concatenation of first and last name.
    current_handle = profile['handle_str']
    assert current_handle == 'angusdoe'
    # handle_str will be invalid as it is 20 characters
    handle_str = '01234567890123456789'
    # Since handle_str is too long, it should raise an input error
    with pytest.raises(InputError):
        user_profile_sethandle(token, handle_str)

def test_invalid_long(register_login):
    # Setting up valid token to be passed into user_profile_sethandle.
    user = register_login
    token = user["token"]
    u_id = user["u_id"]
    profile = user_profile(token, u_id)['user']
    # Current handle should be default concatenation of first and last name.
    current_handle = profile['handle_str']
    assert current_handle == 'angusdoe'
    # handle_str will be invalid as it is greater than 20 characters
    handle_str = 'this_handle_will_be_too_long_to_work'
    # Since handle_str is too long, it should raise an input error
    with pytest.raises(InputError):
        user_profile_sethandle(token, handle_str)
