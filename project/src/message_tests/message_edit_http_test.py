'''
message_edit_http_test.py

Fixtures:
    register_login: registers a new user and logs that user in
    create_channel: creates a public channel

Test Modules:
    test_unauthorised_user_message: fail case where the user editing the message is not a creator of the message or an owner of the channel/flockr
    test_invalid_message_id: fail case where message id is not valid (i.e. the message doesn't exist)
    test_member_edits_own_message: success case where the user editing their message sent the message
    test_owner_edits_user_message: success case owner edits a message in the channel
    test_empty_message: success case where new message request is empty, deleting the message
    test_multiple_edits: success case for when edits are made to multiple messages
'''
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import pytest
import re
from subprocess     import Popen, PIPE
import signal
import requests
import json
import urllib

from error          import InputError, AccessError
from helper         import token_hash
from time           import sleep

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

'''Fail Cases'''
# Scenario: User who is editing the message is not the creator of the message
#           and also isn't the owner of the channel
def test_unauthorised_user_message(url, register_login):
    user = register_login

    # Creating a channel
    r = requests.post(f"{url}/channels/create", json={
        'token': user['token'],
        'name': 'channel',
        'is_public': True
    })
    payload = r.json()
    
    channel_id = payload['channel_id']
    r = requests.post(f"{url}/message/send", json={
        'token': user['token'],
        'channel_id': channel_id,
        'message': "test message 1"
    })
    payload1 = r.json()

    message_id = payload1['message_id']

    # Creating a new user who isnt the owner of the channel, and did not create a message
    requests.post(f"{url}/auth/register", json={
        "email": "test2@email.com",
        "password": "password2",
        "name_first": "Richard2",
        "name_last": "Shen2"
    })

    user2 = requests.post(f"{url}/auth/login", json={
        'email': 'test2@email.com',
        'password': 'password2'
    })
    payload2 = user2.json()

    # Making the second user join the channel
    requests.post(f"{url}/channel/join", json={
        'token': payload2['token'],
        'channel_id': channel_id
    })

    requests.put(f"{url}/message/edit", json={
        'token': payload2['token'],
        'message_id': message_id,
        'message': 'change message'
    })

    queryString = urllib.parse.urlencode({
        'token': payload2['token'],
        'channel_id':channel_id,
        'start': 0
    })
    result = requests.get(f"{url}/channel/messages?{queryString}")

    payload3 = result.json()
    assert payload3['messages'][0]['message'] == 'test message 1'
 
# Testing if the message_id is valid or not
def test_invalid_message_id(url, register_login):
    user = register_login
    is_public = True
    # Creating a channel
    r_channel_create = requests.post(f"{url}/channels/create", json={
        'token': user['token'],
        'name': 'channel',
        'is_public': is_public
    })
    payload = r_channel_create.json()
    
    channel_id = payload['channel_id']
    requests.post(f"{url}/message/send", json={
        'token': user['token'],
        'channel_id': channel_id,
        'message': "test message 1"
    })

    invalid_message_id = -1

    requests.put(f"{url}/message/edit", json={
        'token': user['token'],
        'message_id': invalid_message_id,
        'message': 'change message'
    })

    queryString = urllib.parse.urlencode({
        'token': user['token'],
        'channel_id':channel_id,
        'start': 0
    })
    result = requests.get(f"{url}/channel/messages?{queryString}")
    payload1 = result.json()
    assert payload1['messages'][0]['message'] == 'test message 1'


'''Success Cases'''
# Scenario: The user requesting the edit is not an owner but sent the message
#           originally, therefore has permission to edit.
def test_member_edits_own_message(url, register_login):
    user = register_login
    is_public = True
    # Creating a channel
    r_channel_create = requests.post(f"{url}/channels/create", json={
        'token': user['token'],
        'name': 'channel',
        'is_public': is_public
    })
    payload = r_channel_create.json()
    
    channel_id = payload['channel_id']

    # Creating a new user who isnt the owner of the channel, and did is going to create a message
    requests.post(f"{url}/auth/register", json={
        "email": "test2@email.com",
        "password": "password2",
        "name_first": "Richard2",
        "name_last": "Shen2"
    })

    user2 = requests.post(f"{url}/auth/login", json={
        'email': 'test2@email.com',
        'password': 'password2'
    })
    payload1 = user2.json()

    # Making the second user join the channel
    requests.post(f"{url}/channel/join", json={
        'token': payload1['token'],
        'channel_id': channel_id
    })
    
    r_message_send = requests.post(f"{url}/message/send", json={
        'token': payload1['token'],
        'channel_id': channel_id,
        'message': "test message 1"
    })
    payload2 = r_message_send.json()

    message_id = payload2['message_id']

    requests.put(f"{url}/message/edit", json={
        'token': payload1['token'],
        'message_id': message_id,
        'message': 'change message'
    })

    queryString = urllib.parse.urlencode({
        'token': payload1['token'],
        'channel_id':channel_id,
        'start': 0
    })
    result = requests.get(f"{url}/channel/messages?{queryString}")

    payload3 = result.json()
    assert payload3['messages'][0]['message'] == 'change message'


# Scenario: Owner is able to edit any message in the channel
def test_owner_edits_user_message(url, register_login):
    user = register_login
    is_public = True
    # Creating a channel
    r_channel_create = requests.post(f"{url}/channels/create", json={
        'token': user['token'],
        'name': 'channel',
        'is_public': is_public
    })
    payload = r_channel_create.json()
    
    channel_id = payload['channel_id']

    # Creating a new user who isnt the owner of the channel, and did is going to create a message
    requests.post(f"{url}/auth/register", json={
        "email": "test2@email.com",
        "password": "password2",
        "name_first": "Richard2",
        "name_last": "Shen2"
    })

    user2 = requests.post(f"{url}/auth/login", json={
        'email': 'test2@email.com',
        'password': 'password2'
    })
    payload1 = user2.json()

    # Making the second user join the channel
    requests.post(f"{url}/channel/join", json={
        'token': payload1['token'],
        'channel_id': channel_id
    })

    r_message_send = requests.post(f"{url}/message/send", json={
        'token': payload1['token'],
        'channel_id': channel_id,
        'message': "test message 1"
    })
    payload2 = r_message_send.json()

    message_id = payload2['message_id']

    requests.put(f"{url}/message/edit", json={
        'token': user['token'],
        'message_id': message_id,
        'message': 'channel owner privileges'
    })

    queryString = urllib.parse.urlencode({
        'token': user['token'],
        'channel_id':channel_id,
        'start': 0
    })
    result = requests.get(f"{url}/channel/messages?{queryString}")

    payload3 = result.json()
    assert payload3['messages'][0]['message'] == 'channel owner privileges'

# If the message edit is successful, the original message should now equal to the new message
def test_multiple_edits(url, register_login):
    user = register_login

    # Creating a channel
    r_channel_create = requests.post(f"{url}/channels/create", json={
        'token': user['token'],
        'name': 'channel',
        'is_public': True
    })
    payload = r_channel_create.json()
    
    channel_id = payload['channel_id']

    # Creating a new user who isnt the owner of the channel, and did is going to create a message
    requests.post(f"{url}/auth/register", json={
        "email": "test2@email.com",
        "password": "password2",
        "name_first": "Richard2",
        "name_last": "Shen2"
    })

    user2 = requests.post(f"{url}/auth/login", json={
        'email': 'test2@email.com',
        'password': 'password2'
    })
    payload1 = user2.json()

    # Making the second user join the channel
    requests.post(f"{url}/channel/join", json={
        'token': payload1['token'],
        'channel_id': channel_id
    })

    r_message_send = requests.post(f"{url}/message/send", json={
        'token': payload1['token'],
        'channel_id': channel_id,
        'message': "test message 1"
    })
    payload2 = r_message_send.json()
    message_id = payload2['message_id']

    r_message_send2 = requests.post(f"{url}/message/send", json={
        'token': payload1['token'],
        'channel_id': channel_id,
        'message': "test message 2"
    })
    payload3 = r_message_send2.json()

    message_id2 = payload3['message_id']

    requests.put(f"{url}/message/edit", json={
        'token': payload1['token'],
        'message_id': message_id,
        'message': 'change message 1'
    })

    queryString = urllib.parse.urlencode({
        'token': payload1['token'],
        'channel_id':channel_id,
        'start': 0
    })
    result = requests.get(f"{url}/channel/messages?{queryString}")

    payload4 = result.json()
    assert payload4['messages'][0]['message'] == 'change message 1'

    requests.put(f"{url}/message/edit", json={
        'token': payload1['token'],
        'message_id': message_id2,
        'message': 'change message 2'
    })

    queryString = urllib.parse.urlencode({
        'token': payload1['token'],
        'channel_id':channel_id,
        'start': 0
    })
    result = requests.get(f"{url}/channel/messages?{queryString}")

    payload5 = result.json()
    assert payload5['messages'][1]['message'] == 'change message 2'

def test_flockr_owner_permissions(url, register_login):
    flockr_owner = register_login
    
    # Creating a new user who isnt the owner of the channel, and did is going to create a message
    requests.post(f"{url}/auth/register", json={
        "email": "test2@email.com",
        "password": "password2",
        "name_first": "Richard2",
        "name_last": "Shen2"
    })

    user2 = requests.post(f"{url}/auth/login", json={
        'email': 'test2@email.com',
        'password': 'password2'
    })
    payload = user2.json()
    
    is_public = True
    # Creating a channel
    r_channel_create = requests.post(f"{url}/channels/create", json={
        'token': payload['token'],
        'name': 'channel',
        'is_public': is_public
    })
    payload1 = r_channel_create.json()
    
    channel_id = payload1['channel_id']

    r_message_send = requests.post(f"{url}/message/send", json={
        'token': payload['token'],
        'channel_id': channel_id,
        'message': "test message 1"
    })
    payload2 = r_message_send.json()

    message_id = payload2['message_id']

    requests.put(f"{url}/message/edit", json={
        'token': flockr_owner['token'],
        'message_id': message_id,
        'message': 'flockr owner privileges'
    })

    queryString = urllib.parse.urlencode({
        'token': payload['token'],
        'channel_id':channel_id,
        'start': 0
    })
    result = requests.get(f"{url}/channel/messages?{queryString}")

    payload3 = result.json()
    assert payload3['messages'][0]['message'] == 'flockr owner privileges'
