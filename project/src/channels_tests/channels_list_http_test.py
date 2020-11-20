"""
channels_list__http_test.py

Fixtures:
    register_login_create_channel: creates a user, logs in, creates a channel with that user
    register_login_user2: creates a user2, logs in

Test Modules:
    test_valid_token: creates one channel under a user, runs list and makes sure it retrieves only that one channel
    test_list_multiple_and_only_user: creates 2 channels under user, and another one under user2 and makes sures to only retrieve the 2 channels
    test_invalid_token: given an invalid token expect an AccessError
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import pytest
import re
from subprocess         import Popen, PIPE
import signal
from time               import sleep
import requests
import json
import urllib

from error              import AccessError, InputError
from helper             import token_validator, token_hash

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
def register_login_create_channel(url):
    requests.delete(f"{url}/clear")

    # register and login a user
    r = requests.post(f"{url}/auth/register", json={
        "email":"test@email.com", 
        "password": "password", 
        "name_first": "Angus", 
        "name_last": "Doe"
    })
    payload = r.json()

    r = requests.post(f"{url}/auth/login", json={
        'email': 'test@email.com', 
        'password': 'password'
    })
    payload = r.json()

    token = payload['token']

    r = requests.post(f"{url}/channels/create", json={
        'token': token,
        'name': "test channel",
        'is_public': True
    })

    return token

@pytest.fixture
def register_login_user2(url):

    r = requests.post(f"{url}/auth/register", json={
        "email":"test2@email.com", 
        "password": "password", 
        "name_first": "Bingus", 
        "name_last": "Doe"
    })
    payload = r.json()

    r = requests.post(f"{url}/auth/login", json={
        "email":"test2@email.com", 
        "password": "password", 
    })
    payload = r.json()

    return payload['token']

def test_unretrieved_channel(url, register_login_create_channel, register_login_user2):
    token = register_login_create_channel
    token2 = register_login_user2
   
    # create channel which should not be retrieved
    r = requests.post(f"{url}/channels/create", json={
        'token': token2,
        'name': "unretrieved channel",
        'is_public': True
    })
    payload = r.json()

    queryString = urllib.parse.urlencode({
        "token": token
    })

    r = requests.get(f"{url}/channels/list?{queryString}")
    payload = r.json()
    assert payload == {'channels': [
        {
            'channel_id': 0,
            'name': 'test channel',
            'owner_members': [0],
            'all_members': [0],
            'is_public': True,
            'time_finish': None,
            'messages': [],
        }
    ]}

def test_list_multiple_and_only_user(url, register_login_create_channel, register_login_user2):
    token = register_login_create_channel

    requests.post(f"{url}/channels/create", json={
        'token': token,
        'name': "test2 channel",
        'is_public': True
    })

    token2 = register_login_user2

    requests.post(f"{url}/channels/create", json={
        'token': token2,
        'name': "unretrieved channel",
        'is_public': True
    })

    queryString = urllib.parse.urlencode({
        "token": token
    })
    
    r = requests.get(f"{url}/channels/list?{queryString}")
    payload = r.json()

    assert payload == {'channels': [
        {
            'channel_id': 0,
            'name': 'test channel',
            'owner_members': [0],
            'all_members': [0],
            'is_public': True,
            'time_finish': None,
            'messages': [],
        },
        {
            'channel_id': 1,
            'name': 'test2 channel',
            'owner_members': [0],
            'all_members': [0],
            'is_public': True,
            'time_finish': None,
            'messages': [],
        }
    ]}

def test_invalid_token(url):
    # should throw error since token will be invalid
    token = token_hash(0)

    queryString = urllib.parse.urlencode({
        "token": token
    })
    
    r = requests.get(f"{url}/channels/list?{queryString}")
    payload = r.json()

    assert payload['code'] == 400
