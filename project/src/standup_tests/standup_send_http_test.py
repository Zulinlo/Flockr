'''
standup_send_http_test.py

Fixtures:
    channel_with_user: A user is registered, logged in and owns a channel
    standup: Initiate a standup using the user registered

Helper Modules:
    check_channel_created: verify that the channel has been created

Test Modules:
    - Failure Cases:
    test_invalid_token: raise AccessError because of an invalid token
    test_invalid_c_id: raise InputError when target channel doesn't exist
    test_invalid_message_1001: raise InputError when message is more than 1000 characters
    test_inactive_standup: If there is no currently running standup, raise InputError
    test_external_user: raise AccessError when the user is not a part of the channel

    - Success Cases:
    test_standup_send_multiple: test when multiple standup messages are sent to the standup
    test_standup_send_1000: test valid case when a message containing 1000 characters excluding the handler
    test_standup_send_member: testing standup send from another member in the channel
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

from helper     import token_hash

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
    requests.delete(f"{url}/clear")

    # auth_register("owner@email.com", "password", "Firstname", "Lastname")
    requests.post(f"{url}/auth/register", json={
        "email": "owner@email.com", 
        "password": "password", 
        "name_first": "Firstname", 
        "name_last": "Lastname",
    })
    # user = auth_login("owner@email.com", "password")
    r = requests.post(f"{url}/auth/login", json={
        'email': 'owner@email.com', 
        'password': 'password',
    })
    user = r.json()

    # c_id = channels_create(user['token'], "Channel", True)
    r = requests.post(f"{url}/channels/create", json={
        'token': user['token'],
        'name': 'Channel',
        'is_public': True,
    })
    c_id = r.json()

    return {
        'u_id': user['u_id'], 
        'token': user['token'], 
        'c_id': c_id['channel_id'],
    }

@pytest.fixture
def standup(url, channel_with_user):
    owner = channel_with_user

    # time = standup_start(owner['token'], owner['c_id'], standup_length)
    r = requests.post(f"{url}/standup/start", json={
        'token': owner['token'],
        'channel_id': owner['c_id'],
        'length': 1,
    })
    time = r.json()
    # active = standup_active(owner['token'], owner['c_id'])
    queryString = urllib.parse.urlencode({
        'token': owner['token'], 
        'channel_id': owner['c_id'],
    })
    r = requests.get(f'{url}/standup/active?{queryString}')
    active = r.json()

    return {
        'is_active': active,
        'time_finish': time,
    }

'''Invalid Cases'''
# AccessError: token was invalid
def test_invalid_token(url, channel_with_user, standup):
    sender = channel_with_user
    assert standup['is_active']

    invalid_token = token_hash(-1)

    # with pytest.raises(AccessError):
        # standup_send(invalid_token, sender['c_id'], "Invalid Token")
    r = requests.post(f"{url}/standup/send", json={
        'token': invalid_token,
        'channel_id': sender['c_id'],
        'message': "Invalid Token",
    })
    payload = r.json()

    assert payload['code'] == 400

# InputError: Channel ID is not a valid channel
def test_invalid_c_id(url, channel_with_user, standup):
    assert standup['is_active']
    sender = channel_with_user

    invalid_c_id = -1
    # with pytest.raises(InputError):
    #     standup_send(sender['token'], invalid_c_id, "Invalid Channel ID")
    r = requests.post(f"{url}/standup/send", json={
        'token': sender['token'],
        'channel_id': invalid_c_id,
        'message': "Invalid Channel ID",
    })
    payload = r.json()
    assert payload['code'] == 400

# InputError: Message is more than 1000 characters
def test_invalid_message_1001(url, channel_with_user, standup):
    assert standup['is_active']
    sender = channel_with_user

    invalid_message = "*" * 1001
    assert len(invalid_message) == 1001

    # with pytest.raises(InputError):
    #     standup_send(sender['token'], sender['c_id'], invalid_message)
    r = requests.post(f"{url}/standup/send", json={
        'token': sender['token'],
        'channel_id': sender['c_id'],
        'message': invalid_message,
    })
    payload = r.json()
    assert payload['code'] == 400

# InputError: An active standup is not currently running in this channel
def test_inactive_standup(url, channel_with_user):
    sender = channel_with_user

    # standup = standup_active(sender['token'], sender['c_id'])
    queryString = urllib.parse.urlencode({
        'token': sender['token'], 
        'channel_id': sender['c_id'],
    })
    r = requests.get(f'{url}/standup/active?{queryString}')
    standup = r.json()
    assert not standup['is_active']

    # with pytest.raises(InputError):
    #     standup_send(sender['token'], sender['c_id'], "Test Message")
    r = requests.post(f"{url}/standup/send", json={
        'token': sender['token'],
        'channel_id': sender['c_id'],
        'message': "Inactive Standup",
    })
    payload = r.json()
    assert payload['code'] == 400

# AccessError: Authorised user is not a member of the channel 
#              that the message is within
def test_external_user(url, channel_with_user, standup):
    assert standup['is_active']
    sender = channel_with_user

    # auth_register("member@email.com", "password", "Firstname", "Lastname")
    requests.post(f"{url}/auth/register", json={
        "email":"member@email.com", 
        "password": "password", 
        "name_first": "Firstname", 
        "name_last": "Lastname",
    })
    # member = auth_login("member@email.com", "password")
    r = requests.post(f"{url}/auth/login", json={
        'email': 'member@email.com', 
        'password': 'password',
    })
    member = r.json()
    
    # sender_channel = channel_details(sender['token'], sender['c_id'])
    queryString = urllib.parse.urlencode({
        "token": sender['token'], 
        "channel_id": sender['c_id'],
    })
    r = requests.get(f"{url}/channel/details?{queryString}")
    sender_channel = r.json()

    assert member['u_id'] not in sender_channel['all_members']

    # with pytest.raises(AccessError):
    #     standup_send(member['token'], sender['c_id'], "Test Message")
    r = requests.post(f"{url}/standup/send", json={
        'token': member['token'],
        'channel_id': sender['c_id'],
        'message': "External User",
    })
    payload = r.json()
    assert payload['code'] == 400

'''Success Cases'''
def test_standup_send_multiple(url, channel_with_user, standup):
    assert standup['is_active']
    sender = channel_with_user

    # standup_send(sender['token'], sender['c_id'], "Test Message 1")
    requests.post(f"{url}/standup/send", json={
        'token': sender['token'],
        'channel_id': sender['c_id'],
        'message': "Test Message 1",
    })
    # standup_send(sender['token'], sender['c_id'], "Test Message 2")
    requests.post(f"{url}/standup/send", json={
        'token': sender['token'],
        'channel_id': sender['c_id'],
        'message': "Test Message 2",
    })

    until_standup_finishes = 2 # seconds
    sleep(until_standup_finishes)

    # messages = channel_messages(sender['token'], sender['c_id'], 0)['messages']
    queryString = urllib.parse.urlencode({
        'token': sender['token'], 
        'channel_id': sender['c_id'], 
        'start': 0
    })
    r = requests.get(f"{url}/channel/messages?{queryString}")
    messages = r.json()['messages']

    # handle_str = user_profile(sender['token'], sender['u_id'])['user']['handle_str']
    queryString = urllib.parse.urlencode({
        "token": sender['token'], 
        "u_id": sender['u_id']
    })
    r = requests.get(f"{url}/user/profile?{queryString}")
    handle_str = r.json()['user']['handle_str']

    standup_messages = f"{handle_str}: Test Message 1\n" + f"{handle_str}: Test Message 2"
    assert messages[0]['message'] == standup_messages

def test_standup_send_1000(url, channel_with_user, standup):
    assert standup['is_active']
    sender = channel_with_user
    valid_message = "*" * 1000

    # standup_send(sender['token'], sender['c_id'], valid_message)
    r = requests.post(f"{url}/standup/send", json={
        'token': sender['token'],
        'channel_id': sender['c_id'],
        'message': valid_message,
    })

    until_standup_finishes = 2 # seconds
    sleep(until_standup_finishes)

    # messages = channel_messages(sender['token'], sender['c_id'], 0)['messages']
    queryString = urllib.parse.urlencode({
        'token': sender['token'], 
        'channel_id': sender['c_id'], 
        'start': 0
    })
    r = requests.get(f"{url}/channel/messages?{queryString}")
    messages = r.json()['messages']

    # handle_str = user_profile(sender['token'], sender['u_id'])['user']['handle_str']
    queryString = urllib.parse.urlencode({
        "token": sender['token'], 
        "u_id": sender['u_id']
    })
    r = requests.get(f"{url}/user/profile?{queryString}")
    handle_str = r.json()['user']['handle_str']

    assert messages[0]['message'] == f"{handle_str}: {valid_message}"

def test_standup_send_member(url, channel_with_user, standup):
    assert standup['is_active']
    owner = channel_with_user
    
    # Login and register another user who will send the message
    # auth_register('member@email.com', 'password', 'name_first', 'name_last')
    requests.post(f"{url}/auth/register", json={
        "email":"member@email.com", 
        "password": "password", 
        "name_first": "name_first", 
        "name_last": "name_last",
    })
    # member = auth_login('member@email.com', 'password')
    r = requests.post(f"{url}/auth/login", json={
        'email': 'member@email.com', 
        'password': 'password',
    })
    member = r.json()

    # channel_join(member['token'], owner['c_id'])
    requests.post(f"{url}/channel/join", json={
        'token': member['token'],
        'channel_id': owner['c_id'],
    })

    # standup_send(member['token'], owner['c_id'], "Member Message")
    r = requests.post(f"{url}/standup/send", json={
        'token': member['token'],
        'channel_id': owner['c_id'],
        'message': "Member Message",
    })

    until_standup_finishes = 2 # seconds
    sleep(until_standup_finishes)

    # messages = channel_messages(member['token'], owner['c_id'], 0)['messages']
    queryString = urllib.parse.urlencode({
        'token': member['token'], 
        'channel_id': owner['c_id'], 
        'start': 0
    })
    r = requests.get(f"{url}/channel/messages?{queryString}")
    messages = r.json()['messages']

    # handle_str = user_profile(member['token'], member['u_id'])['user']['handle_str']
    queryString = urllib.parse.urlencode({
        "token": member['token'], 
        "u_id": member['u_id']
    })
    r = requests.get(f"{url}/user/profile?{queryString}")
    handle_str = r.json()['user']['handle_str']

    assert messages[0]['message'] == f"{handle_str}: Member Message"
