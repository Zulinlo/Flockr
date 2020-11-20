'''
user_profile_setemail_test.py

Fixtures:
    register_login: registers and logs in a user and returns their token

Test Modules:
    test_incorrect_email: fail case for the new email being invalid due to no @
    test_invalid_email_no_dot: fail case for the new email being invalid due to no .
    test_preexisting_email: fail case for when the email is the user's prexisting email
    test_diff_user_existing_email: fail case for when another user is already using that email
    test_successful_edit: success case for valid update to email
'''
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import pytest
from implement.user           import user_profile, user_profile_setemail
from implement.auth           import auth_register, auth_login
from error          import InputError
from implement.other          import clear
from helper         import token_hash

@pytest.fixture
def register_login():
    clear()
    auth_register("test@gmail.com", "password", "Richard", "Shen")
    token = auth_login("test@gmail.com", "password")
    return token

'''Test Invalid Cases:'''
# Testing with incorrrect email due to no @, should raise InputError
def test_incorrect_email(register_login):
    user = register_login
    incorrect_email = "incorrectemailgmail.com"
    with pytest.raises(InputError):
        user_profile_setemail(user["token"], incorrect_email)

# Testing with an invalid email, with no dot, should raise InputError
def test_invalid_email_no_dot(register_login):
    user = register_login
    no_dot_email = "invalid@usergmailcom"
    with pytest.raises(InputError):
        user_profile_setemail(user["token"], no_dot_email)

# Testing with the exact email, cannot change the email to a preexisting email, should raise InputError
def test_preexisting_email(register_login):
    user = register_login
    preexisting_email = "test@gmail.com"
    with pytest.raises(InputError):
        user_profile_setemail(user["token"], preexisting_email)

'''Test Success Cases'''
# Testing with a valid and correct email, checking that it should be correct
def test_valid_email(register_login):
    user = register_login
    assert user == {
            'u_id': 0,
            'token': token_hash(0),
        }

# Testing for assertion if the original email was valid and can change to a valid email
def test_successful_edit(register_login):
    user = register_login
    token = user["token"]
    new_email = "newemail@gmail.com"
    user_profile_setemail(token, new_email)

    profile = user_profile(token_hash(0), user['u_id'])['user']['email']

    assert profile == new_email

# Testing for assertion if the original email was valid and can change to a valid email
def test_successful_edit_2(register_login):
    user = register_login
    token = user["token"]
    new_email = "newemail@gmail.com"
    user_profile_setemail(token, new_email)

    profile = user_profile(token_hash(0), user['u_id'])['user']['email']

    assert profile == new_email

    auth_register("test2@gmail.com", "password2", "Richard2", "Shen2")
    token2 = auth_login("test2@gmail.com", "password2")
    new_email2 = "newemail2@gmail.com"
    user_profile_setemail(token2['token'], new_email2)

    profile2 = user_profile(token_hash(0), token2['u_id'])['user']['email']
    assert profile2 == new_email2
