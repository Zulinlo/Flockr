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

import pytest
import re
import signal
import json
import requests
from subprocess     import Popen, PIPE
from time           import sleep

import jwt
from error          import InputError
from implement.auth import auth_register, auth_passwordreset_reset
from helper         import password_hash
from implement.other          import clear

@pytest.fixture
def url():
    url_re = re.compile(r' \* Running on ([^ ]*)')
    server = Popen(["python3", "src/server.py"], stderr=PIPE, stdout=PIPE)
    line = server.stderr.readline()
    local_url = url_re.match(line.decode())
    if local_url:
        yield local_url.group(1)
        # Terminate the server
        server.send_signal(signal.SIGINT)
        waited = 0
        while server.poll() is None and waited < 5:
            sleep(0.1)
            waited += 0.1
        if server.poll() is None:
            server.kill()
    else:
        server.kill()
        raise Exception("Couldn't get URL from local server")

def encoded_resetcode(email):
    SECRET = 'BSOC4THEBOYS'
    encoded_jwt = jwt.encode({'email': email}, SECRET, algorithm='HS256')
    code = encoded_jwt.decode('utf-8')
    return code

'''Success Case'''
def test_password_reset_success(url):
    requests.delete(f"{url}/clear")
    # Register a user
    r = requests.post(f"{url}/auth/register", json={
        "email":"test@email.com", 
        "password": "password", 
        "name_first": "Angus", 
        "name_last": "Doe"
    })
    r = requests.post(f"{url}/auth/login", json={
        'email': 'test@email.com', 
        'password': 'password'
    })
    user = r.json()

    # Retrieve the reset code
    reset_code = encoded_resetcode("test@email.com")

    # Reset the password
    requests.post(f"{url}/auth/passwordreset/reset", json={
        "reset_code": reset_code, 
        "new_password": "newpassword", 
    })
    # Assert that the new password is updated by checking if the hashed versions are the same 
    r = requests.post(f"{url}/auth/logout", json={
        'token': user['token'],
    })
    r = requests.post(f"{url}/auth/login", json={
        'email': 'test@email.com', 
        'password': 'newpassword'
    })
    user = r.json()
    assert user == {
        'u_id': 0,
        'token': user['token'],
    }

'''Fail Cases'''
def test_password_reset_invalid_code(url):
    requests.delete(f"{url}/clear")
    
    invalid_code = encoded_resetcode("unregisted@gmail.com")
    # Fails as the reset code is not valid due to the email belonging to an unregistered user
    r = requests.post(f"{url}/auth/passwordreset/reset", json={
        "reset_code": invalid_code, 
        "new_password": "newpassword", 
    })
    payload = r.json()
    assert payload['code'] == 400


def test_password_reset_invalid_password(url):
    requests.delete(f"{url}/clear")
    # Register a user
    requests.post(f"{url}/auth/register", json={
        "email":"test@email.com", 
        "password": "password", 
        "name_first": "Angus", 
        "name_last": "Doe"
    })
    # Retrieve the reset code
    reset_code = encoded_resetcode("test@gmail.com")
    invalid_password = "pw"
    # Fails as the password is not valid
    r = requests.post(f"{url}/auth/passwordreset/reset", json={
        "reset_code": reset_code, 
        "new_password": invalid_password, 
    })
    payload = r.json()
    assert payload['code'] == 400
