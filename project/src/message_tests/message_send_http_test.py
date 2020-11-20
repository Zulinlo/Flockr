'''
message_send_http_test.py

Fixtures:
    channel_with_user: registers and logs in a user, and then creates a public channel
    get_current_time: returns the current date and time as a timestamp

Test Modules:
    test_invalid_token: fail case for invalid token
    test_invalid_channel_id: fail case for invalid channel id
    test_invalid_message_empty: fail case for empty message
    test_invalid_message_spaces: fail case for message only containing spaces
    test_invalid_message_1001: fail case for exceeding max character limit in message
    test_invalid_sender: fail case for user attempting to message a channel they're not in
    test_message_send_success: success case for messages being sent
    test_message_1000: success case at max character limit
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
def channel_with_user(url):
    # A user is registered, logged in and owns a channel
    requests.delete(f"{url}/clear")
    requests.post(f"{url}/auth/register", json={
        "email":"owner@email.com", 
        "password": "password", 
        "name_first": "Firstname", 
        "name_last": "Lastname",
    })

    user = requests.post(f"{url}/auth/login", json={
        'email': 'owner@email.com', 
        'password': 'password',
    })
    payload = user.json()

    result = requests.post(f"{url}/channels/create", json={
        'token': payload['token'],
        'name': 'Channel',
        'is_public': True,
    })
    payload_c = result.json()

    return {
        'u_id': payload['u_id'],
        'token': payload['token'],
        'c_id': payload_c['channel_id'],
    }

@pytest.fixture
def get_current_time():
    # The current time needs to be obtained in order to compare successful data
    current_time = datetime.utcnow()
    timestamp = int(current_time.replace(tzinfo=timezone.utc).timestamp())
    return timestamp

# Success Cases
####################################################
def test_message_send_success(url, channel_with_user, get_current_time):
    sender = channel_with_user
    timestamp = get_current_time
    
    # Ensure there's no messages in the channel to begin with
    queryString = urllib.parse.urlencode({
        'token': sender['token'], 
        'channel_id': sender['c_id'], 
        'start': 0
    })
    r = requests.get(f'{url}/channel/messages?{queryString}')
    payload = r.json()['messages']
    assert not payload

    # Send the first message
    requests.post(f"{url}/message/send", json={
        'token': sender['token'], 
        'channel_id': sender['c_id'], 
        "message": "Test Message 1"
    })

    queryString = urllib.parse.urlencode({
        'token': sender['token'], 
        'channel_id': sender['c_id'], 
        'start': 0
    })
    r = requests.get(f"{url}/channel/messages?{queryString}")

    messages = r.json()['messages']
    assert messages == [
        {
            'message_id': 0, 
            'u_id': 0, 
            'message': 'Test Message 1', 
            'time_created': timestamp,
            'reacts': [
                {
                    'react_id': 0,
                    'u_ids': [],
                    'is_this_user_reacted': False,
                }
            ],
            'is_pinned': False,
        },
    ]
    
    # Send the second message
    requests.post(f"{url}/message/send", json={
        'token': sender['token'], 
        'channel_id': sender['c_id'], 
        "message": "Test Message 2"
    })

    queryString = urllib.parse.urlencode({
        'token': sender['token'], 
        'channel_id': sender['c_id'], 
        'start': 0
    })
    r = requests.get(f"{url}/channel/messages?{queryString}")

    messages = r.json()['messages']

    assert messages == [
        {
            'message_id': 0, 
            'u_id': 0, 
            'message': 'Test Message 1', 
            'time_created': timestamp,
            'reacts': [
                {
                    'react_id': 0,
                    'u_ids': [],
                    'is_this_user_reacted': False,
                }
            ],
            'is_pinned': False,
            },
        {
            'message_id': 1, 
            'u_id': 0, 
            'message': 'Test Message 2', 
            'time_created': timestamp,
            'reacts': [
                {
                    'react_id': 0,
                    'u_ids': [],
                    'is_this_user_reacted': False,
                }
            ],
            'is_pinned': False,
        },
    ]

def test_message_1000(url, channel_with_user, get_current_time):
    sender = channel_with_user
    timestamp = get_current_time
    valid_message = "*" * 1000

    requests.post(f"{url}/message/send", json={
        'token': sender['token'], 
        'channel_id': sender['c_id'], 
        'message': valid_message
    })

    queryString = urllib.parse.urlencode({
        'token': sender['token'], 
        'channel_id': sender['c_id'], 
        'start': 0
    })
    r = requests.get(f"{url}/channel/messages?{queryString}")
    messages = r.json()['messages']

    assert messages == [
        {
            'message_id': 0, 
            'u_id': 0, 
            'message': valid_message, 
            'time_created': timestamp,
            'reacts': [
                {
                    'react_id': 0,
                    'u_ids': [],
                    'is_this_user_reacted': False,
                }
            ],
            'is_pinned': False,
        },
    ]

def test_multiple_channels(url, channel_with_user, get_current_time):
    sender = channel_with_user
    timestamp = get_current_time

    queryString = urllib.parse.urlencode({
        'token': sender['token'], 
        'channel_id': sender['c_id'], 
        'start': 0
    })
    r = requests.get(f"{url}/channel/messages?{queryString}")
    payload = r.json()['messages']
    
    assert not payload

    requests.post(f"{url}/message/send", json={
        'token': sender['token'], 
        'channel_id': sender['c_id'], 
        'message': "test message 1"
    })

    queryString = urllib.parse.urlencode({
        'token': sender['token'], 
        'channel_id': sender['c_id'], 
        'start': 0
    })
    messages1 = requests.get(f"{url}/channel/messages?{queryString}")
    payload1 = messages1.json()['messages']

    assert payload1 == [
        {
            'message_id': 0, 
            'u_id': sender['u_id'], 
            'message': "test message 1", 
            'time_created': timestamp,
            'reacts': [
                {
                    'react_id': 0,
                    'u_ids': [],
                    'is_this_user_reacted': False,
                }
            ],
            'is_pinned': False,
        },
    ]

    result2 = requests.post(f"{url}/channels/create", json={
        'token': sender['token'],
        'name': 'channel2',
        'is_public': True
    })

    channel2 = result2.json()
    requests.post(f"{url}/message/send", json={
        'token': sender['token'], 
        'channel_id': channel2['channel_id'], 
        'message': "test message 2"
    })

    queryString = urllib.parse.urlencode({
        'token': sender['token'], 
        'channel_id': channel2['channel_id'], 
        'start': 0
    })
    messages2 = requests.get(f"{url}/channel/messages?{queryString}")
    payload2 = messages2.json()['messages']
    assert payload2 == [
        {
            'message_id': 1, 
            'u_id': sender['u_id'], 
            'message': "test message 2", 
            'time_created': timestamp,
            'reacts': [
                {
                    'react_id': 0,
                    'u_ids': [],
                    'is_this_user_reacted': False,
                }
            ],
            'is_pinned': False,
        },
    ]
    
# Invalid Cases
####################################################

def test_invalid_token(url, channel_with_user):
    sender = channel_with_user
    r = requests.post(f"{url}/message/send", json={
        'token': token_hash(1), 
        'channel_id': sender['c_id'], 
        'message': "test message 1"
    })
    payload = r.json()
    assert payload['code'] == 400

def test_invalid_channel_id(url, channel_with_user):
    sender = channel_with_user
    invalid_c_id = -1
    r = requests.post(f"{url}/message/send", json={
        'token': sender['token'], 
        'channel_id': invalid_c_id, 
        'message': "test message 1"
    })
    payload = r.json()
    assert payload['code'] == 400

def test_invalid_message_empty(url, channel_with_user):
    sender = channel_with_user
    empty_message = ""
    r = requests.post(f"{url}/message/send", json={
        'token': sender['token'], 
        'channel_id': sender['c_id'], 
        'message': empty_message
    })
    payload = r.json()
    assert payload['code'] == 400

def test_invalid_message_spaces(url, channel_with_user):
    sender = channel_with_user
    empty_message = " "
    r = requests.post(f"{url}/message/send", json={
        'token': sender['token'], 
        'channel_id': sender['c_id'], 
        'message': empty_message
    })
    payload = r.json()
    assert payload['code'] == 400

def test_invalid_message_1001(url, channel_with_user):
    sender = channel_with_user
    invalid_message = "*" * 1001
    r = requests.post(f"{url}/message/send", json={
        'token': sender['token'], 
        'channel_id': sender['c_id'], 
        'message': invalid_message
    })
    payload = r.json()
    assert payload['code'] == 400

def test_invalid_sender(url, channel_with_user):
    owner = channel_with_user
    requests.post(f"{url}/auth/register", json={
        "email":"invalidsender@email.com", 
        "password": "password", 
        "name_first": "Invalid", 
        "name_last": "Sender"
    })
    sender_token = token_hash(1)
    r = requests.post(f"{url}/message/send", json={'token': sender_token, 'channel_id': owner['c_id'], 'message': "message"})
    payload = r.json()

    assert payload['code'] == 400
