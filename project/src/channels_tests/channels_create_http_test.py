"""
channels_create_http_test.py

Fixtures:
    register_login: creates a user and logs into that user

Helper Modules:
    check_channel_created: verify that the channel has been created

Test Modules:
    test_invalid_token: tests for invalid token
    test_invalid_name_edge_case: tests when channel_name is > 20
    test_invalid_name_empty: tests when name is empty
    test_valid_name_and_token: tests for a valid channel creation
    test_invalid_is_public: tests when is_public is invalid
    test_valid_is_public_true: tests when is_public = True
    test_valid_is_public_false: tests when is_public = False
    test_valid_creator_is_owner: tests if the channel created has the right owner
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import pytest
import re
import signal
import requests
import json
import urllib
from subprocess     import Popen, PIPE
from time           import sleep

from helper         import token_hash

# Use this fixture to get the URL of the server.
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
    requests.post(f"{url}/auth/register", json={
        "email": "test@email.com",
        "password": "password",
        "name_first": "Richard",
        "name_last": "Shen"
    })

    r = requests.post(f"{url}/auth/login", json={
        'email': 'test@email.com', 
        'password': 'password'
    })
    payload = r.json()

    return payload

def check_channel_created(url, token, c_id):

    queryString = urllib.parse.urlencode({
        'token': token
    })
    r = requests.get(f"{url}/channels/listall?{queryString}")
    all_channels = r.json()

    channel_exists = False
    for channel in all_channels['channels']:
        if c_id == channel['channel_id']:
            channel_exists = True

    return channel_exists

def test_invalid_token(url):
    token = token_hash(0)
    r = requests.post(f"{url}/channels/create", json={
        'token': token,
        'name': 'ChannelisValid',
        'is_public': True
    })
    payload = r.json()
    assert payload['code'] == 400

def test_invalid_name_edge_case(url, register_login):
    user = register_login

    # Expect to fail because channel_name is > 20 characters
    r = requests.post(f"{url}/channels/create", json={
        'token': user['token'],
        'name': 'ChannelIsOver20EdgeCase',
        'is_public': True
    })
    payload = r.json()
    assert payload['code'] == 400

def test_invalid_name_empty(url, register_login):
    user = register_login

    r = requests.post(f"{url}/channels/create", json={
        'token': user['token'],
        'name': '',
        'is_public': True
    })
    payload = r.json()
    assert payload['code'] == 400

def test_valid_name_and_token(url, register_login):
    user = register_login

    # Input a dummy channel
    r = requests.post(f"{url}/channels/create", json={
        'token': user['token'],
        'name': 'V4Lid:/42_|}%&*',
        'is_public': True
    })
    c_id = r.json()

    # Check if inserted
    # Scan through all channels to see if channel was created
    channel_exists = check_channel_created(url, user['token'], c_id['channel_id'])

    assert channel_exists

def test_invalid_is_public(url, register_login):
    user = register_login

    # Invalid when is_public is not boolean
    r = requests.post(f"{url}/channels/create", json={
        'token': user['token'],
        'name': 'ValidName1',
        'is_public': 'NotBoolean!'
    })
    payload = r.json()
    assert payload['code'] == 400

def test_valid_is_public_true(url, register_login):
    user = register_login

    # Input a dummy channel
    r = requests.post(f"{url}/channels/create", json={
        'token': user['token'],
        'name': 'ChannelValidUnder20',
        'is_public': True
    })
    c_id = r.json()

    # Check if inserted
    # Scan through all channels to see if channel was created
    channel_exists = check_channel_created(url, user['token'], c_id['channel_id'])

    assert channel_exists

def test_valid_is_public_false(url, register_login):
    user = register_login

    # Input a dummy channel
    r = requests.post(f"{url}/channels/create", json={
        'token': user['token'],
        'name': 'ChannelValidUnder20',
        'is_public': False
    })
    c_id = r.json()

    # Check if inserted
    # Scan through all channels to see if channel was created
    channel_exists = check_channel_created(url, user['token'], c_id['channel_id'])

    assert channel_exists

def test_invalid_creator_is_owner(url, register_login):
    user = register_login

    # c_id = channels_create(user['token'], channel_name, is_public)
    r = requests.post(f"{url}/channels/create", json={
        'token': user['token'],
        'name': 'ChannelValidUnder20',
        'is_public': True
    })
    c_id = r.json()
    
    # Check if inserted
    # Scan through all channels to see if owner exists
    queryString = urllib.parse.urlencode({
        'token': user['token']
    })
    r = requests.get(f"{url}/channels/listall?{queryString}")
    all_channels = r.json()
    
    owner_exists = False
    for channel in all_channels['channels']:
        print(c_id)
        if c_id['channel_id'] == channel['channel_id']:
            if user['u_id'] in channel['owner_members']:
                owner_exists = True

    assert owner_exists
