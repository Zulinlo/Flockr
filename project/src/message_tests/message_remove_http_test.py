'''
message_remove_http_test.py

Fixtures:
    channel_with_user: registers and logs in a user, and then creates a public channel

Test Modules:
    test_owner_message_remove_success: success case for when owner removes their own message
    test_sender_message_remove_success: success case for when sender removes their own message    
    test_owner_removes_sender_message_success: success case for when owner removes a sender's message
    test_multiple_messages_success: success case for when multiple messages sent but one removed
    test_invalid_message_id: fail case for invalid message_id
    test_reused_message_id: fail case for reused message_id
    test_unauthorised_remover: fail case due to unauthorised remover 
'''

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import pytest
import re
from subprocess     import Popen, PIPE
import signal
from time           import sleep
import requests
import json
import urllib

from datetime       import datetime, timezone

# Arguments: token, message_id
# Constraints:
# - Message has to exist
# - Message being removed must be removed by the user who sent it
# - AND/OR the user requesting the remove is an owner of the channel/flockr

# Assumption: message_id is not affected by other messages being removed 
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

# not using current time because workers are too slow to detect the same timestamp from the data and local data when comparing
# @pytest.fixture
# def get_current_time():
    # # The current time needs to be obtained in order to compare successful data
    # # Because workers are too slow to run timestamp again and be the same timestamp between tests
    # timestamp = 101

    # return timestamp

@pytest.fixture
def channel_with_user(url):
    # A user is registered, logged in and owns a channel
    requests.delete(f"{url}/clear")

    requests.post(f"{url}/auth/register", json={
        "email":"owner@email.com", 
        "password": "password", 
        "name_first": "Firstname", 
        "name_last": "Lastname"
    })

    r = requests.post(f"{url}/auth/login", json={
        "email":"owner@email.com", 
        "password": "password", 
    })
    owner = r.json()

    r = requests.post(f"{url}/channels/create", json={
        'token': owner['token'],
        'name': 'Channel',
        'is_public': True
    })
    c_id = r.json()

    return {
        'u_id': owner['u_id'], 
        'token': owner['token'], 
        'c_id': c_id['channel_id'],
    }

'''Success Cases:'''
# Owner of the channel removes their own message
def test_owner_message_remove_success(url, channel_with_user):
    owner = channel_with_user

    # Ensure there's no messages in the channel to begin with
    queryString = urllib.parse.urlencode({
        'token': owner['token'], 
        'channel_id': owner['c_id'], 
        'start': 0
    })
    r = requests.get(f"{url}/channel/messages?{queryString}")
    message = r.json()['messages']
    assert not message

    # Send message 
    r = requests.post(f"{url}/message/send", json={
        'token': owner['token'], 
        'channel_id': owner['c_id'], 
        "message": "Test Message 1"
    })
    message_id = r.json()

    queryString = urllib.parse.urlencode({
        'token': owner['token'], 
        'channel_id': owner['c_id'], 
        'start': 0
    })
    # Verify the message was sent inbetween creating and removing
    r = requests.get(f"{url}/channel/messages?{queryString}")
    message = r.json()['messages']

    assert message[0]['message_id'] == 0
    assert message[0]['u_id'] == 0
    assert message[0]['message'] == 'Test Message 1'

    # Remove message
    requests.delete(f"{url}/message/remove", json={
        'token': owner['token'],
        'message_id': message_id['message_id']
    })

    queryString = urllib.parse.urlencode({
        'token': owner['token'], 
        'channel_id': owner['c_id'], 
        'start': 0
    })
    # Verify that the message was removed
    r = requests.get(f"{url}/channel/messages?{queryString}")
    message = r.json()['messages']
    assert not message

#Pass case for when the sender of a message removes it
def test_sender_message_remove_success(url, channel_with_user):  
    owner = channel_with_user

    # Create second user who will send the message
    requests.post(f"{url}/auth/register", json={
        "email":"user@email.com", 
        "password": "password", 
        "name_first": "First", 
        "name_last": "Last"
    })

    r = requests.post(f"{url}/auth/login", json={
        "email":"user@email.com", 
        "password": "password", 
    })
    sender = r.json()

    requests.post(f"{url}/channel/join", json={
        'token': sender['token'],
        'channel_id': owner['c_id'],
    })

    queryString = urllib.parse.urlencode({
        'token': owner['token'], 
        'channel_id': owner['c_id'], 
        'start': 0
    })
    # Ensure there's no messages in the channel to begin with
    r = requests.get(f"{url}/channel/messages?{queryString}")
    message = r.json()['messages']
    assert not message

    # Send the message with a user other than the owner
    r = requests.post(f"{url}/message/send", json={
        'token': sender['token'], 
        'channel_id': owner['c_id'], 
        "message": "Test Message"
    })
    message_id = r.json()

    queryString = urllib.parse.urlencode({
        'token': owner['token'], 
        'channel_id': owner['c_id'], 
        'start': 0
    })
    # Verify the message was sent inbetween creating and removing
    r = requests.get(f"{url}/channel/messages?{queryString}")
    message = r.json()['messages']


    assert message[0]['message_id'] == 0
    assert message[0]['u_id'] == 1
    assert message[0]['message'] == 'Test Message'

    # Remove message
    requests.delete(f"{url}/message/remove", json={
        'token': sender['token'],
        'message_id': message_id['message_id']
    })

    queryString = urllib.parse.urlencode({
        'token': owner['token'], 
        'channel_id': owner['c_id'], 
        'start': 0
    })
    # Verify that the message was removed
    r = requests.get(f"{url}/channel/messages?{queryString}")
    message = r.json()['messages']
    assert not message

# Sender sends a message and then Owner removes it
def test_message_remove_sender_success(url, channel_with_user):
    owner = channel_with_user

    # Create second user who will send the message
    requests.post(f"{url}/auth/register", json={
        "email":"user@email.com", 
        "password": "password", 
        "name_first": "First", 
        "name_last": "Last"
    })

    r = requests.post(f"{url}/auth/login", json={
        "email":"user@email.com", 
        "password": "password", 
    })
    sender = r.json()

    requests.post(f"{url}/channel/join", json={
        'token': sender['token'],
        'channel_id': owner['c_id'],
    })

    queryString = urllib.parse.urlencode({
        'token': owner['token'], 
        'channel_id': owner['c_id'], 
        'start': 0
    })
    # Ensure there's no messages in the channel to begin with
    r = requests.get(f"{url}/channel/messages?{queryString}")
    message = r.json()['messages']
    assert not message

    # Send the message with a user other than the owner
    r = requests.post(f"{url}/message/send", json={
        'token': sender['token'], 
        'channel_id': owner['c_id'], 
        "message": "Test Message"
    })
    message_id = r.json()

    queryString = urllib.parse.urlencode({
        'token': owner['token'], 
        'channel_id': owner['c_id'], 
        'start': 0
    })
    # Verify the message was sent inbetween creating and removing
    r = requests.get(f"{url}/channel/messages?{queryString}")
    message = r.json()['messages']

    assert message[0]['message_id'] == 0
    assert message[0]['u_id'] == 1
    assert message[0]['message'] == 'Test Message'

    # Remove message
    requests.delete(f"{url}/message/remove", json={
        'token': sender['token'],
        'message_id': message_id['message_id']
    })

    queryString = urllib.parse.urlencode({
        'token': owner['token'], 
        'channel_id': owner['c_id'], 
        'start': 0
    })
    # Verify that the message was removed
    r = requests.get(f"{url}/channel/messages?{queryString}")
    message = r.json()['messages']
    assert not message

# Multiple messages sent but only 1 message removed
def test_multiple_messages_success(url, channel_with_user):
    owner = channel_with_user

    queryString = urllib.parse.urlencode({
        'token': owner['token'], 
        'channel_id': owner['c_id'], 
        'start': 0
    })
    # Ensure there's no messages in the channel to begin with
    r = requests.get(f"{url}/channel/messages?{queryString}")
    message = r.json()['messages']
    assert not message

    # Send 2 messages
    r = requests.post(f"{url}/message/send", json={
        'token': owner['token'], 
        'channel_id': owner['c_id'], 
        "message": "Test Message 1"
    })
    message_to_remove = r.json()

    requests.post(f"{url}/message/send", json={
        'token': owner['token'], 
        'channel_id': owner['c_id'], 
        "message": "Test Message 2"
    })

    queryString = urllib.parse.urlencode({
        'token': owner['token'], 
        'channel_id': owner['c_id'], 
        'start': 0
    })
    # Verify the message was sent inbetween creating and removing
    r = requests.get(f"{url}/channel/messages?{queryString}")
    message = r.json()['messages']

    assert message[0]['message_id'] == 0
    assert message[0]['u_id'] == 0
    assert message[0]['message'] == 'Test Message 1'

    assert message[1]['message_id'] == 1
    assert message[1]['u_id'] == 0
    assert message[1]['message'] == 'Test Message 2'

    # Remove 1st message
    # message_remove(owner['token'], message_to_remove['message_id'])
    requests.delete(f"{url}/message/remove", json={
        'token': owner['token'],
        'message_id': message_to_remove['message_id']
    })

    queryString = urllib.parse.urlencode({
        'token': owner['token'], 
        'channel_id': owner['c_id'], 
        'start': 0
    })
    # Verify that the 2nd message has become the first message in the channel
    r = requests.get(f"{url}/channel/messages?{queryString}")
    message = r.json()['messages']

    assert message[0]['message_id'] == 1
    assert message[0]['u_id'] == 0
    assert message[0]['message'] == 'Test Message 2'

'''Error Cases:'''

# Fail case due to invalid message_id
def test_invalid_message_id(url, channel_with_user):
    owner = channel_with_user

    requests.post(f"{url}/message/send", json={
        'token': owner['token'], 
        'channel_id': owner['c_id'], 
        "message": "Test Message 1"
    })

    invalid_message_id = -1
    r = requests.delete(f"{url}/message/remove", json={
        'token': owner['token'],
        'message_id': invalid_message_id
    })
    payload = r.json()
    assert payload['code'] == 400

# Fail case due to remove being called twice with same message_id (message no longer exists the second time)
def test_reused_message_id(url, channel_with_user):
    owner = channel_with_user

    queryString = urllib.parse.urlencode({
        'token': owner['token'], 
        'channel_id': owner['c_id'], 
        'start': 0
    })
    # Ensure there's no messages in the channel to begin with
    r = requests.get(f"{url}/channel/messages?{queryString}")
    message = r.json()['messages']
    assert not message

    # Send message
    r = requests.post(f"{url}/message/send", json={
        'token': owner['token'], 
        'channel_id': owner['c_id'], 
        "message": "Test Message 1"
    })
    message_id = r.json()

    requests.delete(f"{url}/message/remove", json={
        'token': owner['token'],
        'message_id': message_id['message_id']
    })

    # Failed message removal due to message already having been removed
    r = requests.delete(f"{url}/message/remove", json={
        'token': owner['token'],
        'message_id': message_id['message_id']
    })
    payload = r.json()
    assert payload['code'] == 400

def test_unauthorised_remover(url, channel_with_user):
    owner = channel_with_user

    queryString = urllib.parse.urlencode({
        'token': owner['token'], 
        'channel_id': owner['c_id'], 
        'start': 0
    })
    # Ensure there's no messages in the channel to begin with
    r = requests.get(f"{url}/channel/messages?{queryString}")
    message = r.json()['messages']
    assert not message

    # Send the first message
    r = requests.post(f"{url}/message/send", json={
        'token': owner['token'], 
        'channel_id': owner['c_id'], 
        "message": "Test Message 1"
    })
    message_id = r.json()

    # Register a second user
    requests.post(f"{url}/auth/register", json={
        "email": "unauthorised@gmail.com", 
        "password": "password1", 
        "name_first": "unauthorised", 
        "name_last": "remover"
    })

    r = requests.post(f"{url}/auth/login", json={
        "email":"unauthorised@gmail.com", 
        "password": "password1", 
    })
    unauthorised_remover = r.json()

    requests.post(f"{url}/channel/join", json={
        'token': unauthorised_remover['token'],
        'channel_id': owner['c_id'],
    })

    # Access Error: User trying to remove the message did not send it and is not an owner
    r = requests.delete(f"{url}/message/remove", json={
        'token': unauthorised_remover['token'],
        'message_id': message_id['message_id']
    })
    payload = r.json()
    assert payload['code'] == 400

def test_flockr_owner_remover(url):
    requests.delete(f"{url}/clear")

    # Creating the flockr owner
    requests.post(f"{url}/auth/register", json={
        "email": "flockr_owner@email.com", 
        "password": "flockr_ownerpassword", 
        "name_first": "Firstname", 
        "name_last": "Lastname"
    })

    r = requests.post(f"{url}/auth/login", json={
        "email": "flockr_owner@email.com", 
        "password": "flockr_ownerpassword", 
    })
    flockr_owner = r.json()
    
    # Creating the owner and their own channel
    requests.post(f"{url}/auth/register", json={
        "email": "owner@email.com", 
        "password": "ownerpassword", 
        "name_first": "Firstname", 
        "name_last": "Lastname"
    })

    r = requests.post(f"{url}/auth/login", json={
        "email": "owner@email.com", 
        "password": "ownerpassword", 
    })
    owner = r.json()
    
    r = requests.post(f"{url}/channels/create", json={
        'token': owner['token'],
        'name': 'Channel',
        'is_public': True
    })
    c_id = r.json()

    # Creating the message via the owner
    r = requests.post(f"{url}/message/send", json={
        'token': owner['token'], 
        'channel_id': c_id['channel_id'], 
        "message": "Test Message 1"
    })
    message_id = r.json()
    
    queryString = urllib.parse.urlencode({
        'token': owner['token'], 
        'channel_id': c_id['channel_id'], 
        'start': 0
    })
    r = requests.get(f"{url}/channel/messages?{queryString}")
    message = r.json()['messages']

    assert message[0]['message_id'] == 0
    assert message[0]['u_id'] == 1
    assert message[0]['message'] == 'Test Message 1'

    # Removing the message via the flockr owner
    requests.delete(f"{url}/message/remove", json={
        'token': flockr_owner['token'],
        'message_id': message_id['message_id']
    })

    queryString = urllib.parse.urlencode({
        'token': owner['token'], 
        'channel_id': c_id['channel_id'], 
        'start': 0
    })
    r = requests.get(f"{url}/channel/messages?{queryString}")
    message = r.json()['messages']
    assert not message
    