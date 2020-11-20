"""
channel_messages_test.py

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
from implement.other          import clear
from error          import AccessError, InputError
from implement.auth           import auth_register, auth_login
from implement.channel        import channel_messages
from implement.channels       import channels_create
from implement.message        import message_send
from helper         import token_hash

@pytest.fixture
def get_current_time():
    # The current time needs to be obtained in order to compare successful data
    # Because workers are too slow to run timestamp again and be the same timestamp between tests
    timestamp = 101

    return timestamp

@pytest.fixture
def channel_with_user():
    # A user is registered, logged in and owns a channel
    clear()
    auth_register("owner@email.com", "password", "Firstname", "Lastname")
    token = auth_login("owner@email.com", "password")
    public = True
    c_id = channels_create(token['token'], "Channel", public)

    return {
        'u_id': token['u_id'], 
        'token': token['token'], 
        'c_id': c_id['channel_id'],
    }

@pytest.fixture
def create_messages(channel_with_user, get_current_time):
    owner = channel_with_user
    timestamp = get_current_time

    # Create 60 messages in the owner's channel 
    # To make this black-box, a copy is created so data is not referred to
    messages = []
    i = 0
    while i < 60:
        current_message = 'Example Message ' + str(i)
        message_send(owner['token'], owner['c_id'], current_message)

        messages.append({
            'message_id': i, 
            'u_id': 0, 
            'message': current_message, 
            'time_created': timestamp
        })

        i += 1

    return messages

def test_invalid_token(channel_with_user, create_messages):
    owner = channel_with_user

    with pytest.raises(AccessError):
        channel_messages(token_hash(1), owner['c_id'], 0)

def test_invalid_start(channel_with_user, create_messages):
    owner = channel_with_user
    
    with pytest.raises(InputError):
        channel_messages(owner['token'], owner['c_id'], 61)

def test_valid_start_and_channel_id(channel_with_user, create_messages):
    owner = channel_with_user
    messages = create_messages
    
    message_details = channel_messages(owner['token'], owner['c_id'], 3)
    fetch = {
        'messages': [],
        'start': message_details['start'],
        'end': message_details['end']
    }

    for message in message_details['messages']:
        if 3 <= message['message_id'] <= 53:
            fetch['messages'].append({'message_id': message['message_id'], 'u_id': message['u_id'], 'message': message['message'], 'time_created': 101})

    assert fetch == {'messages': messages[3:53], 'start': 3, 'end': 53}

def test_invalid_channel_id(channel_with_user, create_messages):
    owner = channel_with_user

    invalid_c_id = -1

    with pytest.raises(InputError):
        channel_messages(owner['token'], invalid_c_id, 2)

def test_unauthorised_user(channel_with_user, create_messages):
    owner = channel_with_user

    auth_register("unaurthorised@gmail.com", "password", "Sam", "Wu")
    unaurthorised_user = auth_login("unaurthorised@gmail.com", "password")

    with pytest.raises(AccessError):
        channel_messages(unaurthorised_user['token'], owner['c_id'], 5)

def test_valid_most_recent_message(channel_with_user, create_messages):
    owner = channel_with_user
    messages = create_messages

    message_details = channel_messages(owner['token'], owner['c_id'], 20)
    fetch = {
        'messages': [],
        'start': message_details['start'],
        'end': message_details['end']
    }

    for message in message_details['messages']:
        if 20 <= message['message_id'] <= 60:
            fetch['messages'].append({'message_id': message['message_id'], 'u_id': message['u_id'], 'message': message['message'], 'time_created': 101})

    assert fetch == {'messages': messages[20:60], 'start': 20, 'end': -1}
