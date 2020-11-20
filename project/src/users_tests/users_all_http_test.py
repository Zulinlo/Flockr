"""
users_all_http_test.py

Test Modules:
    test_success_one_user: success case for when there's one user
    test_success_multiple_users: success case for when there's multiple users
    test_fail: fail case due to invalid token
   
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import pytest
import re
import signal
import json
import requests
import urllib

from subprocess     import Popen, PIPE
from time           import sleep
from helper         import password_hash, token_hash

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
        "email":"test@gmail.com", 
        "password": "pass123", 
        "name_first": "Angus", 
        "name_last": "Doe"
    })
    result = requests.post(f"{url}/auth/login", json={
        "email":"test@gmail.com", 
        "password": "pass123"
    })
    payload = result.json()
    return payload

'''Success Cases'''
# Success case when only one user is made
def test_success_one_user(url, register_login):
    user = register_login
    token = user['token']
    queryString = urllib.parse.urlencode({
        "token": token
    })
    result = requests.get(f"{url}/users/all?{queryString}")
    payload = result.json()

    payload['users'][0]['profile_img_url'] = 'default.jpg'
    assert payload == {'users': 
        [{
            'u_id': 0, 
            'email': 'test@gmail.com',
            'name_first': 'Angus',
            'name_last': 'Doe',
            'handle_str': 'angusdoe',
            'profile_img_url': 'default.jpg'
        }]
    }

def test_success_multiple_users(url, register_login):
    register_login
    requests.post(f"{url}/auth/register", json={
        "email":"test2@gmail.com", 
        "password": "pass123", 
        "name_first": "Bangus", 
        "name_last": "Boe"
    })

    result = requests.post(f"{url}/auth/login", json={
        "email":"test2@gmail.com", 
        "password": "pass123"
    })
    user = result.json()
    token = user['token']

    queryString = urllib.parse.urlencode({
        "token": token
    })
    result = requests.get(f"{url}/users/all?{queryString}")
    payload = result.json()

    payload['users'][0]['profile_img_url'] = 'default.jpg'
    payload['users'][1]['profile_img_url'] = 'default.jpg'
    assert payload == {'users': 
        [
            {
                'u_id': 0, 
                'email': 'test@gmail.com',
                'name_first': 'Angus',
                'name_last': 'Doe',
                'handle_str': 'angusdoe',
                'profile_img_url': 'default.jpg'
            },
            {
                'u_id': 1, 
                'email': 'test2@gmail.com',
                'name_first': 'Bangus',
                'name_last': 'Boe',
                'handle_str': 'bangusboe',
                'profile_img_url': 'default.jpg'
            }
        ]
    }

'''Fail Cases'''
def test_invalid_token(url, register_login):
    invalid_token = token_hash(-1)
    queryString = urllib.parse.urlencode({
        "token": invalid_token
    })
    result = requests.get(f"{url}/users/all?{queryString}")
    payload = result.json()
    assert payload['code'] == 400
