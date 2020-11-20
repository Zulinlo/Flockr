"""
user_profile_http_test.py

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
import re
import signal
import json
import requests
import urllib

from helper         import token_hash
from subprocess     import Popen, PIPE
from time           import sleep

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

@pytest.fixture
def register_login(url):
    requests.delete(f"{url}/clear")
    # Fixture registers a user and then logs them in
    # Returns dictionary containing their u_id and token.
    # Create dummy user to make sure right user is being targetted
    requests.post(f"{url}/auth/register", json={
        "email":"ignore@email.com", 
        "password": "password", 
        "name_first": "Bungus", 
        "name_last": "Boe"
    })
    requests.post(f"{url}/auth/register", json={
        "email":"test@gmail.com", 
        "password": "password", 
        "name_first": "Angus", 
        "name_last": "Doe"
    })
    result = requests.post(f"{url}/auth/login", json={
        "email":"test@gmail.com", 
        "password": "password"
    })
    payload = result.json()
    return payload

def test_valid_user(url, register_login):
    # Setting up valid token and u_id to be passed into user_profile.
    user = register_login
    token = user["token"]
    u_id = user["u_id"]

    queryString = urllib.parse.urlencode({
        "token": token, 
        "u_id": u_id
    })
    result = requests.get(f"{url}/user/profile?{queryString}")
    payload = result.json()

    payload['user']['profile_img_url'] = 'default.jpg'

    # Since all inputs are valid, should return the users data. 
    assert payload == {
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

def test_invalid_uid(url, register_login):
    requests.delete(f"{url}/clear")
    # Setting up invalid u_id to be passed into user_profile
    user = register_login
    token = user["token"]

    # u_id is invalid since u_id can only have numerical values.
    # Since u_id is invalid, function should raise an InputError.
    queryString = urllib.parse.urlencode({
        "token": token, 
        "u_id": 25
    })
    result = requests.get(f"{url}/user/profile?{queryString}")
    payload = result.json()
    assert payload['code'] == 400

def test_invalid_token(url, register_login):
    requests.delete(f"{url}/clear")
    # Setting up invalid token to be passed into user_profile.
    user = register_login
    u_id = user["u_id"]
    token = token_hash(1)
    # token is invalid since token can only have numerical values.
    # Since token is invalid, function should raise an InputError.
    queryString = urllib.parse.urlencode({
        "token": token, 
        "u_id": u_id
    })
    result = requests.get(f"{url}/user/profile?{queryString}")
    payload = result.json()
    assert payload['code'] == 400
