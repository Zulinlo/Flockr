"""
auth_register_test.py

Test Modules:
    test_valid_email: test registering user with valid email
    test_invalid_email_no_at: test when email entered has no '@'
    test_invalid_email_no_com: test when email entered has no ".com"
    test_email_exists: test when email entered already been registered
    test_pw_under_six: test when email entered under six characters
    test_invalid_firstname: test when firstname entered is empty
    test_valid_firstname_onechar: test firstname entered as one character
    test_invalid_firstname_long: test when firstname over 50 characters
    test_invalid_lastname_long: test when lastname over 50 characters
    test_valid_lastname_onechar: test lastname entered as one character
    test_invalid_lastname: test when lastname entered is one character
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import pytest
from implement.auth     import auth_register
from error              import InputError
from implement.other              import clear
from helper             import token_hash

# email, password, name_first, name_last
def test_valid_email():
    clear()
    result = auth_register("test@email.com", "password", "Angus", "Doe")
    token = token_hash(0)
    assert result == {
            'u_id': 0,
            'token': token,
        }
    # Testing same concatenation of first & last name to see if unique handle
    # can be generated.
    result = auth_register("test123123@email.com", "password", "Angus", "Doe")
    token = token_hash(1)
    assert result == {
            'u_id': 1,
            'token': token,
        }

def test_invalid_email_no_at():
    clear()
    with pytest.raises(InputError):
        auth_register("testemail.com", "password", "Angus", "Doe")

def test_invalid_email_no_com():
    clear()
    with pytest.raises(InputError):
        auth_register("testemail@gmail", "password", "Angus", "Doe")

def test_email_exists():
    clear()
    auth_register("test2@email.com", "password", "Angus", "Doe")
    with pytest.raises(InputError):
        auth_register("test2@email.com", "password", "Angus", "Doe 2nd")

def test_pw_under_six():
    clear()
    with pytest.raises(InputError):
        auth_register("test@email.com", "pw", "Angus", "Doe")

def test_invalid_firstname():
    clear()
    with pytest.raises(InputError):
        auth_register("test@email.com", "password", "", "Doe")

def test_valid_firstname_onechar():
    clear()
    result = auth_register("test3@email.com", "password", "A", "Doe")
    token = token_hash(0)
    assert result == {
            'u_id': 0,
            'token': token,
        }

def test_invalid_firstname_long():
    clear()
    with pytest.raises(InputError):
        auth_register("test@email.com", "password", "This is over 50 charactersThis is over 50characters", "Doe")

def test_invalid_lastname_long():
    clear()
    auth_register("test2@email.com", "password", "Angus", "Doe")
    with pytest.raises(InputError):
        auth_register("test@email.com", "password", "Angus", "This is over 50 charactersThis is over 50characters")

def test_valid_lastname_onechar():
    clear()
    result = auth_register("test4@email.com", "password", "Angus", "D")
    token = token_hash(0)
    assert result == {
            'u_id': 0,
            'token': token,
        }

def test_invalid_lastname():
    clear()
    with pytest.raises(InputError):
        auth_register("test@email.com", "password", "Angus", "")
