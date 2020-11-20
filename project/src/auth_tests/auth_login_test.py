'''
auth_login_test.py

Test Modules:
    test_auth_valid_login: tests loging in user with valid username and password
    test_auth_invalid_login_email_no_at: test when email entered has no '@'  
    test_auth_invalid_login_email_no_dot: test when email entered has no '.'                                                                                                                                                                                  
    test_auth_invalid_login_email_not_registered: test when email entered not been registered                                                                                                                                                      
    test_auth_invalid_login_wrong_password: test incorrect password entered                                                                                                                                                                          
'''
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import pytest
from implement.auth     import auth_register, auth_login
from error              import InputError
from implement.other              import clear
from helper             import token_hash, password_hash

# email, password
def test_auth_valid_login():
    clear()
    auth_register("testemail@gmail.com", "password", 'John', 'Doe')
    result = auth_login("testemail@gmail.com", 'password')
    token = token_hash(0)
    assert result == {'u_id': 0, 'token': token}

def test_auth_invalid_login_email_no_at():
    clear()
    with pytest.raises(InputError):
        auth_login('testemail.com', 'password')

def test_auth_invalid_login_email_no_dot():
    clear()
    with pytest.raises(InputError):
        auth_login('testemail@gmail', 'password')

def test_auth_invalid_login_email_not_registered():
    clear()
    with pytest.raises(InputError):
        auth_login('notregistered@gmail.com', 'password')

def test_auth_invalid_login_wrong_password():
    clear()
    auth_register('testemail2@gmail.com', 'password', 'Alan', 'Doe')
    with pytest.raises(InputError):
        auth_login('testemail2@gmail.com', 'wrongpassword')

