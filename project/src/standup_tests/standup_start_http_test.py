"""
standup_start_http_test.py

Fixtures:
    register_3_users_channel: registers 2 users and creates a channel which the first user is the owner of and the second user is a member and third user is not a part of, returns c_id and user_id and tokens

Test Modules:
    - Failure Cases:
    test_invalid_token: tests for invalid token
    test_invalid_channel: test for if channel_id is not created
    test_invalid_active_standup: test for if there is already an active standup
    
    - Success Cases:
    test_valid_member: when the user is apart of the valid channel and no active standup is currently running
    test_valid_owner: valid case for when the owner creates the standup
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import pytest
import re
import signal
import json
import requests
import urllib

from datetime       import datetime, timezone
from subprocess     import Popen, PIPE
from time           import sleep

from helper         import token_hash

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
def register_2_users_channel(url):
    requests.delete(f'{url}/clear')
    
    # Create a dummy channel for coverage where code loops through channels
    r = requests.post(f'{url}/auth/register', json={
        'email': 'owner@email.com',
        'password': 'password',
        'name_first': 'Firstname',
        'name_last': 'Lastname',
    })
    owner = r.json()

    requests.post(f'{url}/channels/create', json={
        'token': owner['token'],
        'name': 'Dummy Channel',
        'is_public': True,
    })

    # Create a user who is flockr owner and is creating the channel
    r = requests.post(f'{url}/channels/create', json={
        'token': owner['token'],
        'name': 'Channel',
        'is_public': True,
    })
    c_id = r.json()

    r = requests.post(f'{url}/auth/register', json={
        'email': 'member@gmail.com',
        'password': 'password',
        'name_first': 'Bungus',
        'name_last': 'Two',
    })
    member = r.json()

    requests.post(f'{url}/channel/join', json={
        'token': member['token'],
        'channel_id': c_id['channel_id']
    })

    return {
        'c_id': c_id['channel_id'], 
        'owner': owner, 
        'member': member, 
    }

'''Invalid Cases'''
def test_invalid_token(url, register_2_users_channel):
    channel = register_2_users_channel
    invalid_token = token_hash(-1)
    standup_length = 1

    r = requests.post(f'{url}/standup/start', json={
        'token': invalid_token,
        'channel_id': channel['c_id'],
        'length': standup_length
    })
    payload = r.json()

    assert payload['code'] == 400

def test_invalid_channel(url, register_2_users_channel):
    channel = register_2_users_channel
    invalid_c_id = -1
    standup_length = 1

    r = requests.post(f'{url}/standup/start', json={
        'token': channel['owner']['token'],
        'channel_id': invalid_c_id,
        'length': standup_length
    })
    payload = r.json()

    assert payload['code'] == 400

def test_invalid_active_standup(url, register_2_users_channel):
    channel = register_2_users_channel
    standup_length = 1
    # Start the first standup
    r = requests.post(f'{url}/standup/start', json={
        'token': channel['member']['token'],
        'channel_id': channel['c_id'],
        'length': standup_length
    })
    time_finish = r.json()['time_finish']
    
    queryString = urllib.parse.urlencode({
        'token': channel['member']['token'],
        'channel_id': channel['c_id']
    })
    r = requests.get(f'{url}/standup/active?{queryString}')
    result = r.json()

    assert result == {
        'is_active': True,
        'time_finish': time_finish
    }

    # Ensure that another standup cannot be started
    r = requests.post(f'{url}/standup/start', json={
        'token': channel['owner']['token'],
        'channel_id': channel['c_id'],
        'length': standup_length
    })
    payload = r.json()

    assert payload['code'] == 400

'''Success Cases'''
def test_valid_member(url, register_2_users_channel):
    channel = register_2_users_channel
    standup_length = 1
    
    requests.post(f'{url}/standup/start', json={
        'token': channel['member']['token'],
        'channel_id': channel['c_id'],
        'length': standup_length
    })

    queryString = urllib.parse.urlencode({
        'token': channel['member']['token'],
        'channel_id': channel['c_id']
    })
    r = requests.get(f'{url}/standup/active?{queryString}')
    standup = r.json()

    assert standup['is_active']

def test_valid_owner(url, register_2_users_channel):
    channel = register_2_users_channel
    standup_length = 1

    requests.post(f'{url}/standup/start', json={
        'token': channel['owner']['token'],
        'channel_id': channel['c_id'],
        'length': standup_length
    })

    queryString = urllib.parse.urlencode({
        'token': channel['owner']['token'],
        'channel_id': channel['c_id']
    })
    r = requests.get(f'{url}/standup/active?{queryString}')
    standup = r.json()

    assert standup['is_active']
