'''
auth_logout_test.py

Fixtures:
    register_login: registers a user and logs that user in

Test Modules:
    test_unsuccessful_logout: tests loging out with invalid token
    test_empty_token: test loging out with empty token  
    test_successful_logout: test loging out with valid token                                                                                                                                                                                                                                                                                                                     
'''
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import pytest
from implement.auth     import auth_register, auth_login, auth_logout
from error              import AccessError, InputError
from helper             import token_validator, token_hash
from implement.other              import clear

# Assumptions: User that registers has to log in, in order to logout
@pytest.fixture
def register_login():
    clear()
    auth_register("testemail@gmail.com", "password", "Richard", "Shen")
    user = auth_login("testemail@gmail.com", "password")

    return user

def test_unsuccessful_logout(register_login):
    token = token_hash(1)
    assert auth_logout(token) == {'is_success' : False}

def test_empty_token(register_login):
    token = token_hash(1)
    assert auth_logout(token) == {'is_success' : False}

def test_successful_logout(register_login):
    token = token_hash(0)
    assert auth_logout(token) == {'is_success' : True}
