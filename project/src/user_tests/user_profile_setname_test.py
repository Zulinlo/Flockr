"""
user_profile_setname.py

Fixtures:
    register_login: creates a user and logs into that user

Test Modules:
    test_invalid_token: tests for invalid token
    test_invalid_first_name_too_long: tests edge case for when the first name is 51 characters long
    test_invalid_first_name_too_short: tests edge case for when the first name is 0 characters long
    test_invalid_last_name_too_long: tests edge case for when the last name is 51 characters long
    test_invalid_last_name_too_short: tests edge case for when the last name is 0 characters long
    test_valid_setname: tests for when names are valid and passes
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import pytest
from error          import InputError, AccessError
from implement.other          import clear
from implement.auth           import auth_register, auth_login
from implement.user           import user_profile_setname, user_profile
from helper         import token_hash

@pytest.fixture
def register_login():
    clear()
    auth_register("example@gmail.com", "password", "John", "Doe")
    user = auth_login("example@gmail.com", "password")

    return user

def test_invalid_token(register_login):
    with pytest.raises(AccessError):
        user_profile_setname(token_hash(1), 'Validfirst', 'Validlast')

def test_invalid_first_name_too_long(register_login):
    user = register_login

    first_name_51_characters = 'Abcdefghijklmnopqrstuvwxyasdpoeowoqowowowowowowowow'
    with pytest.raises(InputError):
        user_profile_setname(user['token'], first_name_51_characters, 'Validlast')

def test_invalid_first_name_too_short(register_login):
    user = register_login

    first_name_empty = ''
    with pytest.raises(InputError):
        user_profile_setname(user['token'], first_name_empty, 'Validlast')

def test_invalid_last_name_too_long(register_login):
    user = register_login

    last_name_51_characters = 'Abcdefghijklmnopqrstuvwxyasdpoeowoqowowowowowowowow'
    with pytest.raises(InputError):
        user_profile_setname(user['token'], 'Validfirst', last_name_51_characters)

def test_invalid_last_name_too_short(register_login):
    user = register_login

    last_name_empty = ''
    with pytest.raises(InputError):
        user_profile_setname(user['token'], 'Validfirst', last_name_empty)

def test_valid_setname(register_login):
    # Create previous user to test right user is changed
    register_login

    auth_register("user@email.com", "password", "John", "Boo")
    user = auth_login("user@email.com", "password")

    user_profile_setname(user['token'], 'Second', 'Boe')
    changed_user_info = user_profile(user['token'], user['u_id'])

    # Check if user information has changed
    assert [changed_user_info['user']['name_first'], changed_user_info['user']['name_last']] == ['Second', 'Boe']
