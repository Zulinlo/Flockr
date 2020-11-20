'''
standup_active_http_test.py

Fixtures:
    channel_user_message: A user is registered, logged in and owns a channel
                          which contains a message

Test Modules:
    - Failure Cases:
    test_invalid_token: Raises an AccessError for an invalid token.
    test_invalid_message_id: Raises an InputError if the message_id is not a valid message.
    test_already_pinned: Raises an InputError if Message with ID message_id is already pinned.
    test_external_user_pin: Raises an AccessError if the authorised user is not a member of the channel 
                            that the message is within
    test_unauthorised_user_pin: Raises an AccessError if the authorised user is not an owner.

    - Success Cases:
    test_message_pin_owner: Valid case when channel owner attempts to pin a message
    test_message_pin_flockr_owner: Valid case when flockr owner attempts to pin a message
'''
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import pytest
import re
import signal
import json
import requests
import urllib

from datetime       import datetime, timezone
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
def register_login_channel(url):
    requests.post(f"{url}/auth/register", json={
        "email": "user@email.com", 
        "password": "password", 
        "name_first": "Richard", 
        "name_last": "Shen",
    })

    r = requests.post(f"{url}/auth/login", json={
        'email': 'user@email.com', 
        'password': 'password',
    })
    user = r.json()
    
    r = requests.post(f"{url}/channels/create", json={
        'token': user['token'],
        'name': 'Channel',
        'is_public': True,
    })
    channel_id = r.json()
    return {
        'token': user['token'],
        'channel_id': channel_id['channel_id']
    }

def test_invalid_token(url, register_login_channel):
    channel_id = register_login_channel['channel_id']
    invalid_token = token_hash(-1)

    queryString = urllib.parse.urlencode({
        'token': invalid_token,
        'channel_id': channel_id
    })
    r = requests.get(f"{url}/standup/active?{queryString}")
    payload = r.json()
    assert payload['code'] == 400

def test_inactive_standup(url, register_login_channel):
    token = register_login_channel['token']
    channel_id = register_login_channel['channel_id']

    queryString = urllib.parse.urlencode({
        'token': token,
        'channel_id': channel_id
    })
    r = requests.get(f"{url}/standup/active?{queryString}")
    payload = r.json()
    assert payload == {
        'is_active': False,
        'time_finish': None
    }

def test_2_standups(url, register_login_channel):
    token = register_login_channel['token']
    channel_id = register_login_channel['channel_id']

    r = requests.post(f"{url}/standup/start", json={
        'token': token,
        'channel_id': channel_id,
        'length': 1
    })

    time_finish = r.json()['time_finish']

    queryString = urllib.parse.urlencode({
        'token': token,
        'channel_id': channel_id
    })
    r = requests.get(f"{url}/standup/active?{queryString}")
    payload1 = r.json()
    assert payload1 == {
        'is_active': True,
        'time_finish': time_finish
    }
    until_standup_finishes = 2
    sleep(until_standup_finishes)

    queryString = urllib.parse.urlencode({
        'token': token,
        'channel_id': channel_id
    })
    r = requests.get(f"{url}/standup/active?{queryString}")
    payload2 = r.json()
    assert payload2 == {
        'is_active': False,
        'time_finish': None
    }

    r = requests.post(f"{url}/standup/start", json={
        'token': token,
        'channel_id': channel_id,
        'length': 1
    })
    time_finish = r.json()['time_finish']

    queryString = urllib.parse.urlencode({
        'token': token,
        'channel_id': channel_id
    })
    r = requests.get(f"{url}/standup/active?{queryString}")
    payload3 = r.json()
    assert payload3 == {
        'is_active': True,
        'time_finish': time_finish
    }

    sleep(until_standup_finishes)
    
    queryString = urllib.parse.urlencode({
        'token': token,
        'channel_id': channel_id
    })
    r = requests.get(f"{url}/standup/active?{queryString}")
    payload4 = r.json()
    assert payload4 == {
        'is_active': False,
        'time_finish': None
    }
