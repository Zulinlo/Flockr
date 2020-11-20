"""
channels_listall_http_test.py

Fixtures:
    register_login_create_channel: creates a user, logs in, creates a channel with that user

Test Modules:
    test_valid_token: test when token passed through is valid, i.e. corresponds to registered and logged in user
    test_list_multiple: test when 3 channels created under user
    test_invalid_token: test when token passed through is invalid, i.e. not corresponding to registered and logged in user

"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import pytest
import re
import signal
import json
import requests
import urllib

from error          import InputError, AccessError
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
def register_login_create_channel(url):
    requests.delete(f"{url}/clear")
    requests.post(f"{url}/auth/register", json={"email":"test@email.com", "password": "password", "name_first": "Angus", "name_last": "Doe"})
    result = requests.post(f"{url}/auth/login", json={"email":"test@email.com", "password": "password"})
    token = token_hash(0)
    requests.post(f"{url}/channels/create", json={"token":token, "name": "test", "is_public": True})
    payload = result.json()
    return payload

def test_valid_token(url, register_login_create_channel):
    user = register_login_create_channel
    token = user['token']
    queryString = urllib.parse.urlencode({
        "token": token
    })
    result = requests.get(f"{url}/channels/listall?{queryString}")
    payload = result.json()
    assert payload == {'channels': [
            {
                'channel_id': 0,
                'name': 'test',
                'owner_members': [0],
                'all_members': [0],
                'is_public': True,
                'time_finish': None,
                'messages': [],
            }
        ]
    }

def test_list_multiple(url, register_login_create_channel):
    user = register_login_create_channel
    token = user['token']
    requests.post(f"{url}/channels/create", json={"token":token, "name": "test2", "is_public": True})
    requests.post(f"{url}/channels/create", json={"token":token, "name": "test3", "is_public": True})
    queryString = urllib.parse.urlencode({
        "token": token
    })
    result = requests.get(f"{url}/channels/listall?{queryString}")
    payload = result.json()
    assert payload == {'channels': [
            {
                'channel_id': 0,
                'name': 'test',
                'owner_members': [0],
                'all_members': [0],
                'is_public': True,
                'time_finish': None,
                'messages': [],
            },
            {
                'channel_id': 1,
                'name': 'test2',
                'owner_members': [0],
                'all_members': [0],
                'is_public': True,
                'time_finish': None,
                'messages': [],
            },
            {
                'channel_id': 2,
                'name': 'test3',
                'owner_members': [0],
                'all_members': [0],
                'is_public': True,
                'time_finish': None,
                'messages': [],
            }
        ]
    }

def test_invalid_token(url, register_login_create_channel):
    invalid_token = token_hash(-1)
    queryString = urllib.parse.urlencode({
        "token": invalid_token
    })
    result = requests.get(f"{url}/channels/listall?{queryString}")
    payload = result.json()
    print(payload)
    assert payload['code'] == 400
