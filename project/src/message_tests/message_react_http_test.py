'''
message_react_http_test.py

Fixtures:
    create_channel_and_message: registers and logs in a user, and then creates a public channel and message

Test Modules:
    test_invalid_message: fail case where the message_id does not have a valid message in the channel
    test_invalid_react_id: fail case where the react_id is not valid (has to be equal to 1)
    test_fail_react: fail case where the message with ID message_id already contains a react with ID react_id
    test_successful_react: success case where the message gets a react
    test_successful_react_same_message_twice: success case where another user reacts to a message which has already been reacted to
    test_successful_react_two_messages: success case where two messages are created, and both get reacts
'''
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import pytest
import re
import signal
import json
import requests
import urllib
from datetime   import datetime, timezone
from subprocess import Popen, PIPE

from time       import sleep
from implement.channel    import channel_messages 

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

# Creates the user, channel, and message as a fixture to be passed into other functions
@pytest.fixture
def create_channel_and_message(url):
    requests.delete(f"{url}/clear")
    
    requests.post(f"{url}/auth/register", json={
        "email":"user@email.com", 
        "password": "password", 
        "name_first": "Richard", 
        "name_last": "Shen",
    })

    r = requests.post(f"{url}/auth/login", json={
        'email': 'user@email.com', 
        'password': 'password',
    })
    owner = r.json()

    r = requests.post(f"{url}/channels/create", json={
        'token': owner['token'],
        'name': 'Channel',
        'is_public': True
    })
    channel_id = r.json()

    r = requests.post(f"{url}/message/send", json={
        'token': owner['token'], 
        'channel_id': channel_id['channel_id'], 
        "message": "Test Message 1"
    })
    message = r.json()

    return {
        'u_id': owner['u_id'], 
        'token': owner['token'], 
        'channel_id': channel_id['channel_id'],
        'message_id': message['message_id'],
    }

# Testing if the message has a valid message_id
def test_invalid_message(url, create_channel_and_message):
    token = create_channel_and_message['token']
    invalid_message_id = -1
    react_id = 1
    r = requests.post(f"{url}/message/react", json={
        'token': token, 
        'message_id': invalid_message_id,
        'react_id': react_id
    })
    payload = r.json()
    assert payload['code'] == 400

# Testing that the user is in the channel
def test_user_not_in_channel(url, create_channel_and_message):
    message_id = create_channel_and_message['message_id']
    requests.post(f"{url}/auth/register", json={
        "email":"user2@email.com", 
        "password": "password2", 
        "name_first": "Richard2", 
        "name_last": "Shen2",
    })

    r = requests.post(f"{url}/auth/login", json={
        'email': 'user2@email.com', 
        'password': 'password2',
    })
    user2 = r.json()
    react_id = 1
    user2_token = user2['token']

    r = requests.post(f"{url}/message/react", json={
        'token': user2_token, 
        'message_id': message_id,
        'react_id': react_id
    })
    payload = r.json()
    assert payload['code'] == 400

# Testing the react_id is valid
def test_invalid_react_id(url, create_channel_and_message):
    token = create_channel_and_message['token']
    message_id = create_channel_and_message['message_id']
    invalid_react_id = -1
    r = requests.post(f"{url}/message/react", json={
        'token': token, 
        'message_id': message_id,
        'react_id': invalid_react_id
    })
    payload = r.json()
    assert payload['code'] == 400

# Testing that the message was not reacted twice by the same user
def test_fail_react(url, create_channel_and_message):
    token = create_channel_and_message['token']
    message_id = create_channel_and_message['message_id']
    react_id = 1
    requests.post(f"{url}/message/react", json={
        'token': token, 
        'message_id': message_id,
        'react_id': react_id
    })
    r = requests.post(f"{url}/message/react", json={
        'token': token, 
        'message_id': message_id,
        'react_id': react_id
    })
    payload = r.json()
    assert payload['code'] == 400

# Testing if the message can be reacted to successfully 
def test_successful_react(url, create_channel_and_message):
    token = create_channel_and_message['token']
    message_id = create_channel_and_message['message_id']
    channel_id = create_channel_and_message['channel_id']
    react_id = 1
    requests.post(f"{url}/message/react", json={
        'token': token, 
        'message_id': message_id,
        'react_id': react_id
    })
    # In order to call a requests.get, you have to use a query string which is passed
    # through to the request
    queryString = urllib.parse.urlencode({
        'token': token,
        'channel_id': channel_id,
        'start': 0
    })
    r = requests.get(f"{url}/channel/messages?{queryString}")
    payload = r.json()['messages'][0]
    assert payload['reacts'][0]['react_id'] == 1

# Testing if the two users can react to the same message
def test_successful_react_same_message_twice(url, create_channel_and_message):
    token = create_channel_and_message['token']
    message_id = create_channel_and_message['message_id']
    channel_id = create_channel_and_message['channel_id']
    react_id = 1
    requests.post(f"{url}/message/react", json={
        'token': token, 
        'message_id': message_id,
        'react_id': react_id
    })
    # Creating the second user 
    requests.post(f"{url}/auth/register", json={
        "email":"user2@email.com", 
        "password": "password2", 
        "name_first": "Richard2", 
        "name_last": "Shen2",
    })

    r = requests.post(f"{url}/auth/login", json={
        'email': 'user2@email.com', 
        'password': 'password2',
    })
    user2 = r.json()
    user2_token = user2['token']

    requests.post(f"{url}/channel/join", json={
        'token': user2_token,
        'channel_id': create_channel_and_message['channel_id']
    })

    requests.post(f"{url}/message/react", json={
        'token': user2_token, 
        'message_id': message_id,
        'react_id': react_id
    })

    queryString = urllib.parse.urlencode({
        'token': token,
        'channel_id': channel_id,
        'start': 0
    })
    r = requests.get(f"{url}/channel/messages?{queryString}")
    payload = r.json()['messages'][0]
    # Testing that the u_ids have both the users inside, meaning they both reacted to the message
    assert payload['reacts'][0]['u_ids'] == [0, 1]

# Testing if the user can react to two messages
def test_successful_react_two_messages(url, create_channel_and_message):
    token = create_channel_and_message['token']
    channel_id = create_channel_and_message['channel_id']
    message_id = create_channel_and_message['message_id']
    r = requests.post(f"{url}/message/send", json={
        'token': token, 
        'channel_id': channel_id, 
        "message": "Test Message 2"
    })
    message = r.json()
    message_id2 = message['message_id']

    react_id = 1
    requests.post(f"{url}/message/react", json={
        'token': token, 
        'message_id': message_id,
        'react_id': react_id
    })
    queryString = urllib.parse.urlencode({
        'token': token,
        'channel_id': channel_id,
        'start': 0
    })
    r = requests.get(f"{url}/channel/messages?{queryString}")
    payload = r.json()['messages'][0]
    assert payload['reacts'][0]['react_id'] == 1

    requests.post(f"{url}/message/react", json={
        'token': token, 
        'message_id': message_id2,
        'react_id': react_id
    })
    queryString = urllib.parse.urlencode({
        'token': token,
        'channel_id': channel_id,
        'start': 0
    })
    r = requests.get(f"{url}/channel/messages?{queryString}")
    # Changing the key of the messages to 1 since a new message is created, hence accessed differently
    payload = r.json()['messages'][1]
    assert payload['reacts'][0]['react_id'] == 1

