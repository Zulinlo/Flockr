"""
channel_messages_http_test.py

Fixtures:
    register_login_channels_messages: creates a user and login to the user, also creates 60 dummy messages, in order to have a comparison to the actual function

Test Modules:
    test_invalid_token: expects the invalid token to have an AssertError
    test_invalid_start: expects InputError because start is greater than the total number of messages in the channel
    test_valid_start_and_channel_id: given valid input then make sure the function returns correct values
    test_invalid_channel_id: expects InputError because input Channel ID is not valid
    test_unauthorised_user: expects AccessError because authorised user is not a member of channel with channel_id
    test_valid_most_recent_message: expects a return -1 because the ending message is within the end id which the function wants to return
"""

import pytest
import re
import signal
import json
import requests
import urllib
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
def get_current_time():
    # The current time needs to be obtained in order to compare successful data
    # Because workers are too slow to run timestamp again and be the same timestamp between tests
    timestamp = 101

    return timestamp

@pytest.fixture
def channel_with_user(url):
    # A user is registered, logged in and owns a channel
    requests.delete(f"{url}/clear")
    
    requests.post(f"{url}/auth/register", json={
        "email": "owner@email.com", 
        "password": "password", 
        "name_first": "Firstname", 
        "name_last": "Lastname"
    })
    result = requests.post(f"{url}/auth/login", json={
        "email": "owner@email.com", 
        "password": "password"
    })
    token = result.json()
    public = True

    c_id = requests.post(f"{url}/channels/create", json={
        "token": token['token'], 
        "name": "Channel", 
        "is_public": public
    })
    payload = c_id.json()

    return {
        'u_id': token['u_id'], 
        'token': token['token'], 
        'c_id': payload['channel_id'],
    }

@pytest.fixture
def create_messages(url, channel_with_user, get_current_time):
    owner = channel_with_user
    timestamp = get_current_time

    # Create 60 messages in the owner's channel 
    # To make this black-box, a copy is created so data is not referred to
    messages = []
    i = 0
    while i < 60:
        current_message = 'Example Message ' + str(i)
        requests.post(f"{url}/message/send", json={
            'token': owner['token'], 
            'channel_id': owner['c_id'], 
            'message': current_message
        })

        messages.append({
            'message_id': i, 
            'u_id': 0, 
            'message': current_message, 
            'time_created': timestamp
        })

        i += 1

    return messages

def test_invalid_token(url, channel_with_user, create_messages):
    owner = channel_with_user
    
    invalid_token = -1
    token = token_hash(invalid_token)

    queryString = urllib.parse.urlencode({
        'token': token, 
        'channel_id': owner['c_id'], 
        'start': 0
    })

    result = requests.get(f"{url}/channel/messages?{queryString}")
    payload = result.json()

    assert payload['code'] == 400

def test_invalid_start(url, channel_with_user, create_messages):
    owner = channel_with_user

    queryString = urllib.parse.urlencode({
        'token': owner['token'], 
        'channel_id': owner['c_id'], 
        'start': 61
    })

    result = requests.get(f"{url}/channel/messages?{queryString}")
    payload = result.json()

    assert payload['code'] == 400

def test_valid_start_and_channel_id(url, channel_with_user, create_messages):
    owner = channel_with_user
    messages = create_messages

    queryString = urllib.parse.urlencode({
        'token': owner['token'], 
        'channel_id': owner['c_id'], 
        'start': 3
    })
    
    r = requests.get(f"{url}/channel/messages?{queryString}")
    payload = r.json()

    fetch = {
        'messages': [],
        'start': payload['start'],
        'end': payload['end'],
    }

    # Because timestamp takes too long to compare
    for message in payload['messages']:
        if 3 <= message['message_id'] <= 53:
            fetch['messages'].append({
                'message_id': message['message_id'], 
                'u_id': message['u_id'], 
                'message': message['message'], 
                'time_created': 101
            })


    assert fetch == {'messages': messages[3:53], 'start':  3, 'end': 53}

def test_invalid_channel_id(url, channel_with_user, create_messages):
    owner = channel_with_user

    invalid_c_id = -1

    queryString = urllib.parse.urlencode({
        'token': owner['token'], 
        'channel_id': invalid_c_id, 
        'start': 2
    })

    result = requests.get(f"{url}/channel/messages?{queryString}")
    payload = result.json()

    assert payload['code'] == 400

def test_unauthorised_user(url, channel_with_user, create_messages):
    owner = channel_with_user
    
    requests.post(f"{url}/auth/register", json={
        "email": "unaurthorised@gmail.com", 
        "password": "password", 
        "name_first": "Sam", 
        "name_last": "Wu"
    })
    result = requests.post(f"{url}/auth/login", json={
        "email": "unaurthorised@gmail.com", 
        "password": "password"
    })
    unaurthorised_user = result.json()

    queryString = urllib.parse.urlencode({
        'token': unaurthorised_user['token'], 
        'channel_id': owner['c_id'], 
        'start': 5
    })

    message = requests.get(f"{url}/channel/messages?{queryString}")
    payload = message.json()

    assert payload['code'] == 400 

def test_valid_most_recent_message(url, channel_with_user, create_messages):
    owner = channel_with_user
    messages = create_messages

    queryString = urllib.parse.urlencode({
        'token': owner['token'], 
        'channel_id': owner['c_id'], 
        'start': 20
    })

    r = requests.get(f"{url}/channel/messages?{queryString}")
    payload = r.json()

    fetch = {
        'messages': [],
        'start': payload['start'],
        'end': payload['end'],
    }

    # Because timestamp takes too long to compare
    for message in payload['messages']:
        if 20 <= message['message_id'] <= 60:
            fetch['messages'].append({
                'message_id': message['message_id'], 
                'u_id': message['u_id'], 
                'message': message['message'], 
                'time_created': 101
            })

    assert fetch == {'messages': messages[20:60], 'start': 20, 'end': -1}
