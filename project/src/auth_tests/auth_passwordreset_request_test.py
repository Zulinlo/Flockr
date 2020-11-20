"""
auth_passwordreset_request_test.py

Fixtures:
    register: creates two users but does not log them in.

Test Modules:
    test_valid_user: success case for when email corresponds with registered user
    test_valid_user2: success case for when email corresponds with registered user
    test_invalid_user: fail case for when email doesn't correspond with registered user
    test_invalid_user2: fail case for when email doesn't correspond with registered user
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import pytest
from implement.auth import auth_register, auth_passwordreset_request
from implement.other          import clear

@pytest.fixture
def register():
    # Fixture registers two users but does not log them in
    # No return value
    # Create dummy users for email testing
    clear()
    auth_register("1531.mangoteam3@gmail.com", "password", "Angus", "Doe")
    auth_register("1531mango.team3@gmail.com", "password", "Angus", "Boe")

def test_valid_user(register):
    register 
    email = "1531.mangoteam3@gmail.com"
    result = auth_passwordreset_request(email)
    # Request always returns {} but email with code will be sent
    assert result == {}

def test_valid_user2(register):
    register 
    email = "1531mango.team3@gmail.com"
    result = auth_passwordreset_request(email)
    # Request always returns {} but email with code will be sent
    assert result == {}

def test_invalid_user(register):
    register 
    email = "invalid@gmail.com"
    result = auth_passwordreset_request(email)
    # Request always returns {} but email with code will be sent
    assert result == {}

def test_invalid_user2(register):
    register 
    email = "doesntexist@gmail.com@gmail.com"
    result = auth_passwordreset_request(email)
    # Request always returns {} but email with code will be sent
    assert result == {}