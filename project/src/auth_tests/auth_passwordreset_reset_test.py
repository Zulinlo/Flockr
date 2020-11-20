"""
auth_passwordreset_reset_test.py

Fixtures:
    encoded_resetcode: returns an encoded version of the reset password code
Test Modules:
    test_password_reset_success: Success case where code works and password is valid
    test_password_reset_invalid_code: Fail case where code is invalid
    test_password_reset_invalid_password: Fail case where code works but password is under six characters
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

from error  import InputError
from implement.auth   import auth_register, auth_login, auth_logout, auth_passwordreset_reset
from helper import password_hash
import jwt
import pytest
from implement.other import clear

def encoded_resetcode(email):
    SECRET = 'BSOC4THEBOYS'
    encoded_jwt = jwt.encode({'email': email}, SECRET, algorithm='HS256')
    code = encoded_jwt.decode('utf-8')
    return code

'''Success Case'''
def test_password_reset_success():
    clear()
    # Register 2 users for coverage
    auth_register("dummy@gmail.com", "password", "Wilson", "Doe")['u_id']
    auth_register("test@gmail.com", "password", "Wilson", "Doe")['u_id']
    user = auth_login("test@gmail.com", "password")

    # Retrieve the reset code
    reset_code = encoded_resetcode("test@gmail.com")
    # Reset the password
    auth_passwordreset_reset(reset_code, "newpassword")
    # Assert that the new password is updated by checking if the hashed versions are the same 

    auth_logout(user['token'])
    user = auth_login("test@gmail.com", "newpassword")
    assert user == {
        'u_id': 1,
        'token': user['token'],
    }

'''Fail Cases'''
def test_password_reset_invalid_code():
    clear()
    invalid_code = encoded_resetcode("unregisted@gmail.com")
    # Fails as the reset code is not valid due to the email belonging to an unregistered user
    with pytest.raises(InputError):
        auth_passwordreset_reset(invalid_code, "newpassword")    

def test_password_reset_invalid_password():
    clear()
    # Register a user
    auth_register("test@gmail.com", "password", "Wilson", "Doe")
    auth_login("test@gmail.com", "password")
    # Retrieve the reset code
    reset_code = encoded_resetcode("test@gmail.com")
    invalid_password = "pw"
    # Fails as the password is not valid
    with pytest.raises(InputError):
        auth_passwordreset_reset(reset_code, invalid_password)
