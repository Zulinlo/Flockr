'''
message_sendlater_http_test.py

Fixtures:
    channel_with_user: registers and logs in a user, and then creates a public channel
    get_current_time: returns the current date and time as a timestamp

Test Modules:
    test_message_sendlater_success: success case for messages being sent at correct time
    def test_message_sendtwolater_success: success case for two identical messages queued for same time having distinct message_id's
    test_message_1000: success case at max character limit
    test_multiple_messages: success case with multiple messages queued up at the same time
    test_invalid_token: fail case for invalid token
    test_invalid_channel_id: fail case for invalid channel id
    test_invalid_message_empty: fail case for empty message
    test_invalid_message_spaces: fail case for message only containing spaces
    test_invalid_message_1001: fail case for exceeding max character limit in message
    test_invalid_sender: fail case for user attempting to message a channel they're not in
    test_invalid_time: fail case for user scheduling a message for the past
'''
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import pytest
from implement.message    import message_sendlater
from error      import AccessError, InputError
from implement.other      import clear
from implement.auth       import auth_register, auth_login
from implement.channels   import channels_create
from implement.channel    import channel_messages
from datetime   import datetime, timezone
from time       import sleep
from helper     import token_hash

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

# Arguments: token, channel_id, message, time_sent
# Assumptions:
# - A user cannot send empty messages such as "" or "  "
# - The sender has to be apart of the channel to send a message
# - A user can send messages to a channel which only contains themselves in it.
# - The time when the message is scheduled to be sent must be in the future

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

'''Success Cases'''
def test_message_sendlater_success(url, channel_with_user, get_current_time):
    sender = channel_with_user
    current_timestamp = get_current_time
    later_timestamp = current_timestamp + 3
    even_later_timestamp = current_timestamp + 5
   
    # Ensure there's no messages in the channel to begin with
    # assert not channel_messages(sender['token'], sender['c_id'], 0)['messages']
    queryString = urllib.parse.urlencode({
        'token': sender['token'], 
        'channel_id': sender['c_id'], 
        'start': 0
    })
    r = requests.get(f'{url}/channel/messages?{queryString}')
    messages = r.json()['messages']
    assert not messages

    # Queue up multiple message
    #message_sendlater(sender['token'], sender['c_id'], "Test Message 1", later_timestamp)
    requests.post(f"{url}/message/sendlater", json={
        'token': sender['token'], 
        'channel_id': sender['c_id'],
        "message": "Test Message 1",
        'time_sent': later_timestamp,
    })
    #message_sendlater(sender['token'], sender['c_id'], "Test Message 2", even_later_timestamp)
    requests.post(f"{url}/message/sendlater", json={
        'token': sender['token'], 
        'channel_id': sender['c_id'], 
        "message": "Test Message 2",
        'time_sent': even_later_timestamp,
    })
    # Check that no messages have been sent yet
    # assert not channel_messages(sender['token'], sender['c_id'], 0)['messages']
    queryString = urllib.parse.urlencode({
        'token': sender['token'], 
        'channel_id': sender['c_id'], 
        'start': 0
    })
    r = requests.get(f'{url}/channel/messages?{queryString}')
    messages = r.json()['messages']
    assert not messages

    # Wait 3 seconds before checking if first message has been sent
    sleep(3)

    # messages = channel_messages(sender['token'], sender['c_id'], 0)['messages']
    queryString = urllib.parse.urlencode({
        'token': sender['token'], 
        'channel_id': sender['c_id'], 
        'start': 0
    })
    r = requests.get(f'{url}/channel/messages?{queryString}')
    messages = r.json()['messages']
    assert messages == [
        {
            'message_id': 0, 
            'u_id': 0, 
            'message': 'Test Message 1', 
            'time_created': later_timestamp,
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

    # Wait another 2 seconds to see if second message has been sent
    sleep(2)
    # messages = channel_messages(sender['token'], sender['c_id'], 0)['messages']
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
            'time_created': later_timestamp,
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
            'time_created': even_later_timestamp,
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
    
def test_message_sendtwolater_success(url, channel_with_user, get_current_time):
    sender = channel_with_user
    current_timestamp = get_current_time
    later_timestamp = current_timestamp + 3
   
    # Ensure there's no messages in the channel to begin with
    # assert not channel_messages(sender['token'], sender['c_id'], 0)['messages']

    queryString = urllib.parse.urlencode({
        'token': sender['token'], 
        'channel_id': sender['c_id'], 
        'start': 0
    })
    r = requests.get(f'{url}/channel/messages?{queryString}')
    payload = r.json()['messages']
    assert not payload

    # Queue up multiple messages which are the same, at the same time

    # message_sendlater(sender['token'], sender['c_id'], "Test Message", later_timestamp)
    requests.post(f"{url}/message/sendlater", json={
        'token': sender['token'], 
        'channel_id': sender['c_id'], 
        "message": "Test Message",
        "time_sent": later_timestamp,
    })

    # message_sendlater(sender['token'], sender['c_id'], "Test Message", later_timestamp)
    requests.post(f"{url}/message/sendlater", json={
        'token': sender['token'], 
        'channel_id': sender['c_id'], 
        "message": "Test Message",
        "time_sent": later_timestamp,
    })

    # Check that no messages have been sent yet
    # assert not channel_messages(sender['token'], sender['c_id'], 0)['messages']
    queryString = urllib.parse.urlencode({
        'token': sender['token'], 
        'channel_id': sender['c_id'], 
        'start': 0
    })
    r = requests.get(f'{url}/channel/messages?{queryString}')
    payload = r.json()['messages']
    assert not payload

    # Wait 4 seconds (buffer time) before checking if both messages were sent
    # with distinct message_id
    sleep(4)

    # messages = channel_messages(sender['token'], sender['c_id'], 0)['messages']
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
            'message':'Test Message', 
            'time_created': later_timestamp,
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
            'message': 'Test Message', 
            'time_created': later_timestamp,
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
    current_timestamp = get_current_time
    later_timestamp = current_timestamp + 3
    valid_message = "*" * 1000

    # Queue up the message to be sent later
    # message_sendlater(sender['token'], sender['c_id'], valid_message, later_timestamp)
    requests.post(f"{url}/message/sendlater", json={
        'token': sender['token'], 
        'channel_id': sender['c_id'], 
        "message": valid_message,
        "time_sent": later_timestamp,
    })
    # Check that no messages have been sent yet
    # assert not channel_messages(sender['token'], sender['c_id'], 0)['messages']
    queryString = urllib.parse.urlencode({
        'token': sender['token'], 
        'channel_id': sender['c_id'], 
        'start': 0
    })
    r = requests.get(f'{url}/channel/messages?{queryString}')
    payload = r.json()['messages']
    assert not payload
    
    # Wait 5 seconds to see if messages have been sent (including buffer time)
    sleep(5)
    # messages = channel_messages(sender['token'], sender['c_id'], 0)['messages']
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
            'time_created': later_timestamp,
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

# Ensure that the message_id is unique, even across channels
def test_multiple_channels(url, channel_with_user, get_current_time):
    sender = channel_with_user
    current_timestamp = get_current_time
    later_timestamp = current_timestamp + 3

    # Ensure there's no messages in the channel to begin with
    # assert not channel_messages(sender['token'], sender['c_id'], 0)['messages']
    queryString = urllib.parse.urlencode({
        'token': sender['token'], 
        'channel_id': sender['c_id'], 
        'start': 0
    })
    r = requests.get(f'{url}/channel/messages?{queryString}')
    messages = r.json()['messages']
    assert not messages

    # Send the first message to the first channel
    # message_sendlater(sender['token'], sender['c_id'], "Test Message 1", later_timestamp)
    requests.post(f"{url}/message/sendlater", json={
        'token': sender['token'], 
        'channel_id': sender['c_id'], 
        "message": "Test Message 1",
        'time_sent': later_timestamp,
    })

    # Check that no messages have been sent yet in first channel
    # assert not channel_messages(sender['token'], sender['c_id'], 0)['messages']
    queryString = urllib.parse.urlencode({
        'token': sender['token'], 
        'channel_id': sender['c_id'], 
        'start': 0
    })
    r = requests.get(f'{url}/channel/messages?{queryString}')
    messages = r.json()['messages']
    assert not messages

    # Create second channel
    # channel_2 = channels_create(sender['token'], "Channel 2", public)['channel_id']
    c = requests.post(f"{url}/channels/create", json={
        'token': sender['token'],
        'name': 'Channel 2',
        'is_public': True,
    })
    channel_2 = c.json()['channel_id']

    # Send the second message in the second channel
    # message_sendlater(sender['token'], channel_2, "Test Message 2", later_timestamp)
    requests.post(f"{url}/message/sendlater", json={
        'token': sender['token'], 
        'channel_id': channel_2, 
        "message": "Test Message 2",
        'time_sent': later_timestamp,
    })

    # Check that no messages have been sent yet in the second channel
    # assert not channel_messages(sender['token'], channel_2, 0)['messages']
    queryString = urllib.parse.urlencode({
        'token': sender['token'], 
        'channel_id': channel_2, 
        'start': 0
    })
    payload2 = requests.get(f"{url}/channel/messages?{queryString}")
    messages2 = payload2.json()['messages']
    assert not messages2

    # Wait 5 seconds to see if messages have been sent (additional buffer time)
    sleep(5)

    queryString = urllib.parse.urlencode({
        'token': sender['token'], 
        'channel_id': sender['c_id'], 
        'start': 0
    })
    payload1 = requests.get(f'{url}/channel/messages?{queryString}')
    messages = payload1.json()['messages']

    queryString = urllib.parse.urlencode({
        'token': sender['token'], 
        'channel_id': channel_2, 
        'start': 0
    })
    r = requests.get(f"{url}/channel/messages?{queryString}")
    messages2 = r.json()['messages']

    # messages = channel_messages(sender['token'], sender['c_id'], 0)['messages']
    assert messages == [
        {
            'message_id': 0, 
            'u_id': 0, 
            'message': 'Test Message 1', 
            'time_created': later_timestamp,
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
    # messages2 = channel_messages(sender['token'], channel_2, 0)['messages']
    assert messages2 == [
        {
            'message_id': 1, 
            'u_id': 0, 
            'message': 
            'Test Message 2', 
            'time_created': later_timestamp,
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

# Test Invalid Cases:
######################################################

# AccessError: token passed in does not refer to a valid user.
def test_invalid_token(url, channel_with_user, get_current_time):
    sender = channel_with_user
    current_timestamp = get_current_time
    later_timestamp = current_timestamp + 3
    
    # with pytest.raises(AccessError):
    #     message_sendlater(token_hash(-1), sender['c_id'], "Test Message", later_timestamp)
    r = requests.post(f"{url}/message/sendlater", json={
        'token': token_hash(-1),
        'channel_id': sender['c_id'],
        "message": "Test Message",
        'time_sent': later_timestamp,
    })
    payload = r.json()
    assert payload['code'] == 400

# InputError: channel_id does not refer to a valid channel.
def test_invalid_channel_id(url, channel_with_user, get_current_time):
    sender = channel_with_user
    current_timestamp = get_current_time
    later_timestamp = current_timestamp + 3
    invalid_c_id = -1
    
    # with pytest.raises(InputError):
    #     message_sendlater(sender['token'], invalid_c_id, "Test Message", later_timestamp)
    r = requests.post(f"{url}/message/sendlater", json={
        'token': sender['token'], 
        'channel_id': invalid_c_id,
        "message": "Test Message",
        'time_sent': later_timestamp,
    })
    payload = r.json()
    assert payload['code'] == 400

# InputError: Cannot send empty messsages
def test_invalid_message_empty(url, channel_with_user, get_current_time):
    sender = channel_with_user
    current_timestamp = get_current_time
    later_timestamp = current_timestamp + 3
    empty_message = ""
    # with pytest.raises(InputError):
    #     message_sendlater(sender['token'], sender['c_id'], empty_message, later_timestamp)
    r = requests.post(f"{url}/message/sendlater", json={
        'token': sender['token'], 
        'channel_id': sender['c_id'],
        "message": empty_message,
        'time_sent': later_timestamp,
    })
    payload = r.json()
    assert payload['code'] == 400

# InputError: Cannot send empty messsages with 'whitespace'
def test_invalid_message_spaces(url, channel_with_user, get_current_time):
    sender = channel_with_user
    current_timestamp = get_current_time
    later_timestamp = current_timestamp + 3
    empty_message = "  "
    # with pytest.raises(InputError):
    #     message_sendlater(sender['token'], sender['c_id'], empty_message, later_timestamp)
    r = requests.post(f"{url}/message/sendlater", json={
        'token': sender['token'], 
        'channel_id': sender['c_id'],
        "message": empty_message,
        'time_sent': later_timestamp,
    })
    payload = r.json()
    assert payload['code'] == 400

# InputError: Message is more than 1000 characters
def test_invalid_message_1001(url, channel_with_user, get_current_time):
    sender = channel_with_user
    current_timestamp = get_current_time
    later_timestamp = current_timestamp + 3

    invalid_message = "*" * 1001
    # with pytest.raises(InputError):
    #     message_sendlater(sender['token'], sender['c_id'], invalid_message, later_timestamp)
    r = requests.post(f"{url}/message/sendlater", json={
        'token': sender['token'], 
        'channel_id': sender['c_id'],
        "message": invalid_message,
        'time_sent': later_timestamp,
    })
    payload = r.json()
    assert payload['code'] == 400

# AccessError: The authorised user has not joined the channel that they are 
#              are trying to post to
def test_invalid_sender(url, channel_with_user, get_current_time):
    owner = channel_with_user
    current_timestamp = get_current_time
    later_timestamp = current_timestamp + 3
    # Seperate user who is not in the channel
    # auth_register("invalid_sender@email.com", "password", "Firstname", "Lastname")
    requests.post(f"{url}/auth/register", json={
        "email": "invalid_sender@email.com",
        "password": "password", 
        "name_first": "Firstname", 
        "name_last": "Lastname",
    })

    # invalid_sender = auth_login("invalid_sender@email.com", "password")
    r = requests.post(f"{url}/auth/login", json={
        'email': 'invalid_sender@email.com', 
        'password': 'password',
    })
    invalid_sender = r.json()

    # with pytest.raises(AccessError):
    #     message_sendlater(invalid_sender['token'], owner['c_id'], "Test Message", later_timestamp)
    r = requests.post(f"{url}/message/sendlater", json={
        'token': invalid_sender['token'], 
        'channel_id': owner['c_id'],
        "message": "Test Message",
        'time_sent': later_timestamp,
    })
    payload = r.json()
    assert payload['code'] == 400

# Input Error: The user is trying to send a time in the past
def test_invalid_time(url, channel_with_user, get_current_time):
    sender = channel_with_user
    current_timestamp = get_current_time
    # Set the time as a time in the past
    past_timestamp = current_timestamp - 3
    # with pytest.raises(InputError):
    #     message_sendlater(sender['token'], sender['c_id'], "Test Message", past_timestamp)
    r = requests.post(f"{url}/message/sendlater", json={
        'token': sender['token'], 
        'channel_id': sender['c_id'],
        "message": "Test Message",
        'time_sent': past_timestamp,
    })
    payload = r.json()
    assert payload['code'] == 400