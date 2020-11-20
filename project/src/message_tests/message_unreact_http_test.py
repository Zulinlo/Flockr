'''
message_unreact_http_test.py

Fixtures:
    register_login: registers a new user and logs that user in
    create_channel_and_message_react: creates a public channel, 
                                      then creates a message to be reacted with react_id 1
    

Test Modules:
    test_successful_unreact: success case where reacted message is unreacted
    test_successful_unreact_two_reacts: success case where two reacted messages are unreacted
    test_invalid_messageid: fail case where the message_id does not have a valid message in the channel
    test_user_not_in_channel: fail case where user is trying to unreact message in channel they're not in
    test_invalid_react_id: fail case where the react_id is not valid (has to be equal to 1)
    test_unreact_noreacts: fail case where trying to unreact a messasge with no reacts.
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

# Creates/logs in the user, channel, a reacted message as a fixture to be passed into other functions
@pytest.fixture
def create_channel_and_message_react(url):
    requests.delete(f"{url}/clear")
    
    requests.post(f"{url}/auth/register", json={
        "email":"user@email.com", 
        "password": "password", 
        "name_first": "Angus", 
        "name_last": "Doe",
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
        "message": "Hello Anto"
    })
    message = r.json()

    react_id = 1
    requests.post(f"{url}/message/react", json={
        'token': owner['token'], 
        'message_id': channel_id['channel_id'],
        'react_id': react_id
    })

    return {
        'u_id': owner['u_id'], 
        'token': owner['token'], 
        'channel_id': channel_id['channel_id'],
        'message_id': message['message_id'],
    }

''' Success Cases '''
def test_successful_unreact(url, create_channel_and_message_react):
    token = create_channel_and_message_react['token']
    message_id = create_channel_and_message_react['message_id']
    channel_id = create_channel_and_message_react['channel_id']

    # u_id of 0 should be in u_ids list
    queryString = urllib.parse.urlencode({
        'token': token,
        'channel_id': channel_id,
        'start': 0
    })

    r = requests.get(f"{url}/channel/messages?{queryString}")
    payload = r.json()['messages'][0]['reacts']
    assert payload[0]['u_ids'] == [0]

    react_id = 1
    requests.post(f"{url}/message/unreact", json={
        'token': token, 
        'message_id': message_id,
        'react_id': react_id
    })

    # u_id of 0 should be removed from u_id list.
    queryString = urllib.parse.urlencode({
        'token': token,
        'channel_id': channel_id,
        'start': 0
    })

    r = requests.get(f"{url}/channel/messages?{queryString}")
    payload = r.json()['messages'][0]['reacts']
    assert payload[0]['u_ids'] == []

def test_successful_unreact_two_reacts(url, create_channel_and_message_react):
    token = create_channel_and_message_react['token']
    message_id = create_channel_and_message_react['message_id']
    channel_id = create_channel_and_message_react['channel_id']

    # u_id of 0 should be in u_ids list
    queryString = urllib.parse.urlencode({
        'token': token,
        'channel_id': channel_id,
        'start': 0
    })

    r = requests.get(f"{url}/channel/messages?{queryString}")
    payload = r.json()['messages'][0]['reacts']
    assert payload[0]['u_ids'] == [0]

    react_id = 1
    requests.post(f"{url}/message/unreact", json={
        'token': token, 
        'message_id': message_id,
        'react_id': react_id
    })

    # u_id of 0 should be removed from u_id list.
    queryString = urllib.parse.urlencode({
        'token': token,
        'channel_id': channel_id,
        'start': 0
    })
    r = requests.get(f"{url}/channel/messages?{queryString}")
    payload = r.json()['messages'][0]['reacts']
    assert payload[0]['u_ids'] == []

    r = requests.post(f"{url}/message/send", json={
        'token': token, 
        'channel_id': channel_id, 
        "message": "Hello Again Anto"
    })
    message = r.json()
    message_id = message['message_id']
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
    payload = r.json()['messages'][1]['reacts']
    assert payload[0]['u_ids'] == [0]

    requests.post(f"{url}/message/unreact", json={
        'token': token, 
        'message_id': message_id,
        'react_id': react_id
    })

    # u_id of 0 should be removed from u_id list.
    r = requests.get(f"{url}/channel/messages?{queryString}")
    payload = r.json()['messages'][1]['reacts']
    assert payload[0]['u_ids'] == []

''' Fail Cases '''
def test_invalid_messageid(url, create_channel_and_message_react):
    token = create_channel_and_message_react['token']
    invalid_message_id = -1
    react_id = 1
    r = requests.post(f"{url}/message/unreact", json={
        'token': token, 
        'message_id': invalid_message_id,
        'react_id': react_id
    })
    payload = r.json()
    assert payload['code'] == 400

def test_user_not_in_channel(url, create_channel_and_message_react):
    message_id = create_channel_and_message_react['message_id']

    requests.post(f"{url}/auth/register", json={
        "email":"user2@email.com", 
        "password": "password", 
        "name_first": "Angus2", 
        "name_last": "Doe2",
    })

    r = requests.post(f"{url}/auth/login", json={
        'email': 'user2@email.com', 
        'password': 'password',
    })
    user2 = r.json()['token']
    react_id = 1
    r = requests.post(f"{url}/message/unreact", json={
        'token': user2, 
        'message_id': message_id,
        'react_id': react_id
    })
    payload = r.json()
    assert payload['code'] == 400

def test_invalid_react_id(url, create_channel_and_message_react):
    token = create_channel_and_message_react['token']
    message_id = create_channel_and_message_react['message_id']
    channel_id = create_channel_and_message_react['channel_id']

    # u_id of 0 should be in u_ids list
    queryString = urllib.parse.urlencode({
        'token': token,
        'channel_id': channel_id,
        'start': 0
    })

    r = requests.get(f"{url}/channel/messages?{queryString}")
    payload = r.json()['messages'][0]['reacts']
    assert payload[0]['u_ids'] == [0]

    react_id = -1
    r = requests.post(f"{url}/message/unreact", json={
        'token': token, 
        'message_id': message_id,
        'react_id': react_id
    })
    payload = r.json()
    assert payload['code'] == 400

def test_unreact_noreacts(url):
    requests.delete(f"{url}/clear")
    
    requests.post(f"{url}/auth/register", json={
        "email":"user@email.com", 
        "password": "password", 
        "name_first": "Angus", 
        "name_last": "Doe",
    })

    r = requests.post(f"{url}/auth/login", json={
        'email': 'user@email.com', 
        'password': 'password',
    })
    owner = r.json()

    # creating public channel
    r = requests.post(f"{url}/channels/create", json={
        'token': owner['token'],
        'name': 'Channel',
        'is_public': True
    })
    channel_id = r.json()

    # send a message but no reacts
    r = requests.post(f"{url}/message/send", json={
        'token': owner['token'], 
        'channel_id': channel_id['channel_id'], 
        "message": "Hello Anto"
    })
    message = r.json()
    react_id = 1
    
    # should fail because unreacting message with no reacts
    r = requests.post(f"{url}/message/unreact", json={
        'token': owner['token'], 
        'message_id': message['message_id'],
        'react_id': react_id
    })
    payload = r.json()
    assert payload['code'] == 400


