'''
message_pin_http_test.py

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
def channel_user_message(url):
    requests.delete(f"{url}/clear")

    r = requests.post(f"{url}/auth/register", json={
        "email": "flockrowner@email.com", 
        "password": "password", 
        "name_first": "John", 
        "name_last": "Doe",
    })
    flockr_owner = r.json()
    
    requests.post(f"{url}/auth/register", json={
        "email": "owner@email.com", 
        "password": "password", 
        "name_first": "Firstname", 
        "name_last": "Lastname",
    })

    r = requests.post(f"{url}/auth/login", json={
        'email': 'owner@email.com', 
        'password': 'password',
    })
    owner = r.json()

    r = requests.post(f"{url}/channels/create", json={
        'token': owner['token'],
        'name': 'Channel',
        'is_public': True,
    })
    c_id = r.json()

    r = requests.post(f"{url}/message/send", json={
        'token': owner['token'], 
        'channel_id': c_id['channel_id'], 
        "message": "Test Message 1"
    })
    message = r.json()

    return {
        'u_id': owner['u_id'], 
        'token': owner['token'], 
        'flockr_owner_token': flockr_owner['token'],
        'c_id': c_id['channel_id'],
        'message_id': message['message_id']
    }

'''Invalid Cases'''
# AccessError: Invalid Token
def test_invalid_token(url, channel_user_message):
    owner = channel_user_message

    invalid_token = token_hash(2)
    r = requests.post(f"{url}/message/pin", json={
        'token': invalid_token, 
        'message_id': owner['message_id'],
    })
    payload = r.json()
    assert payload['code'] == 400

# InputError: message_id is not a valid message
def test_invalid_message_id(url, channel_user_message):
    owner = channel_user_message

    invalid_m_id = -1
    r = requests.post(f"{url}/message/pin", json={
        'token': owner['token'], 
        'message_id': invalid_m_id,
    })
    payload = r.json()
    assert payload['code'] == 400

# InputError: Message with ID message_id is already pinned
def test_already_pinned(url, channel_user_message):
    owner = channel_user_message

    queryString = urllib.parse.urlencode({
        'token': owner['token'],
        'query_str': "Test Message 1"
    })
    r = requests.get(f"{url}/search?{queryString}")

    message = r.json()['messages']
    assert not message[0]['is_pinned']

    requests.post(f"{url}/message/pin", json={
        'token': owner['token'], 
        'message_id': owner['message_id'],
    })

    queryString = urllib.parse.urlencode({
        'token': owner['token'],
        'query_str': "Test Message 1"
    })
    r = requests.get(f"{url}/search?{queryString}")

    message = r.json()['messages']
    assert message[0]['is_pinned']

    # Pin the same message
    r = requests.post(f"{url}/message/pin", json={
        'token': owner['token'], 
        'message_id': owner['message_id'],
    })
    payload = r.json()
    assert payload['code'] == 400

# AccessError: Authorised user is not a member of the channel 
#              that the message is within
def test_external_user_pin(url, channel_user_message):
    owner = channel_user_message

    requests.post(f"{url}/auth/register", json={
        "email": "member@email.com", 
        "password": "password", 
        "name_first": "Firstname", 
        "name_last": "Lastname",
    })

    r = requests.post(f"{url}/auth/login", json={
        'email': 'member@email.com', 
        'password': 'password',
    })
    member = r.json()

    queryString = urllib.parse.urlencode({
        "token": owner['token'], 
        "channel_id": owner['c_id']
    })
    r = requests.get(f"{url}/channel/details?{queryString}")

    owner_channel = r.json()
    assert member['u_id'] not in owner_channel['all_members']

    r = requests.post(f"{url}/message/pin", json={
        'token': member['token'], 
        'message_id': owner['message_id'],
    })
    payload = r.json()
    assert payload['code'] == 400

# AccessError: Authorised user is not an owner
def test_unauthorised_user_pin(url, channel_user_message):
    owner = channel_user_message

    requests.post(f"{url}/auth/register", json={
        "email": "member@email.com", 
        "password": "password", 
        "name_first": "Firstname", 
        "name_last": "Lastname",
    })

    r = requests.post(f"{url}/auth/login", json={
        'email': 'member@email.com', 
        'password': 'password',
    })
    member = r.json()

    requests.post(f"{url}/channel/join", json={
        'token': member['token'],
        'channel_id': owner['c_id'],
    })

    queryString = urllib.parse.urlencode({
        "token": owner['token'], 
        "channel_id": owner['c_id']
    })
    r = requests.get(f"{url}/channel/details?{queryString}")

    owner_channel = r.json()
    assert member['u_id'] not in owner_channel['all_members']

    r = requests.post(f"{url}/message/pin", json={
        'token': member['token'], 
        'message_id': owner['message_id'],
    })
    payload = r.json()
    assert payload['code'] == 400

'''Success Cases'''
def test_message_pin_owner(url, channel_user_message):
    owner = channel_user_message

    queryString = urllib.parse.urlencode({
        'token': owner['token'],
        'query_str': "Test Message 1"
    })
    r = requests.get(f"{url}/search?{queryString}")

    message = r.json()['messages']

    assert not message[0]['is_pinned']
    
    requests.post(f"{url}/message/pin", json={
        'token': owner['token'], 
        'message_id': owner['message_id'],
    })

    queryString = urllib.parse.urlencode({
        'token': owner['token'],
        'query_str': "Test Message 1"
    })
    r = requests.get(f"{url}/search?{queryString}")

    message = r.json()['messages']

    assert message[0]['is_pinned']

def test_message_pin_flockr_owner(url, channel_user_message):
    owner = channel_user_message

    queryString = urllib.parse.urlencode({
        'token': owner['token'],
        'query_str': "Test Message 1"
    })
    r = requests.get(f"{url}/search?{queryString}")

    message = r.json()['messages']

    assert not message[0]['is_pinned']
    
    requests.post(f"{url}/message/pin", json={
        'token': owner['flockr_owner_token'], 
        'message_id': owner['message_id'],
    })

    queryString = urllib.parse.urlencode({
        'token': owner['token'],
        'query_str': "Test Message 1"
    })
    r = requests.get(f"{url}/search?{queryString}")

    message = r.json()['messages']

    assert message[0]['is_pinned']
