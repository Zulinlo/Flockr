'''
message_react_test.py

Fixtures:
    register_login: registers a new user and logs that user in
    create_channel: creates a public channel
    message_create: creates a message in the public channel

Test Modules:
    test_invalid_message: fail case where the message_id does not have a valid message in the channel
    test_invalid_react_id: fail case where the react_id is not valid (has to be equal to 1)
    test_fail_react: fail case where the message with ID message_id already contains a react with ID react_id
    test_successful_react: success case where the message gets a react
    test_successful_react_same_message_twice: sucess case where another user reacts to a message which has already been reacted to
    test_successful_react_two_messages: success case where two messages are created, and both get reacts
'''
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import pytest
from error          import InputError
from implement.other          import clear
from implement.auth           import auth_register, auth_login
from implement.channels       import channels_create
from implement.channel        import channel_join, channel_details, channel_messages
from implement.message        import message_send, message_react

@pytest.fixture
def register_login():
    # Using the clear function in the register_login fixture so it won't have to be called after
    clear()
    auth_register("user@email.com", "password", "Richard", "Shen")
    user = auth_login("user@email.com", "password")
    return {
        "u_id": user["u_id"],
        "token": user["token"]
    }

@pytest.fixture
def create_channel_and_message(register_login):
    # register a user and log them in so they have a token.
    user = register_login
    token = user['token']
    is_public = True
    channel_id = channels_create(token, "Channel", is_public)
    message_example = 'test message 1'
    message = message_send(token, channel_id['channel_id'], message_example)
    message_details = channel_messages(token, channel_id['channel_id'], 0)['messages']

    return {
        'channel_id': channel_id['channel_id'],
        'message_id': message['message_id'],
        'reacts': message_details[0]['reacts']
    }

''' Fail Cases '''
def test_invalid_message(register_login, create_channel_and_message):
    token = register_login['token']
    create_channel_and_message['channel_id']
    invalid_message_id = -1
    react_id = 1
    with pytest.raises(InputError):
        message_react(token, invalid_message_id, react_id)

def test_user_not_in_channel(register_login, create_channel_and_message):
    message_id = create_channel_and_message['message_id']
    # Creating a second channel which will not have the messages, and make a new user 
    auth_register("user2@email.com", "password2", "Richard2", "Shen2")
    user2 = auth_login("user2@email.com", "password2")
    user2_token = user2['token']
    
    react_id = 1
    with pytest.raises(InputError):
        message_react(user2_token, message_id, react_id)

def test_invalid_react_id(register_login, create_channel_and_message):
    token = register_login['token']
    create_channel_and_message['channel_id']
    message_id = create_channel_and_message['message_id']
    invalid_react_id = -1
    with pytest.raises(InputError):
        message_react(token, message_id, invalid_react_id)

def test_fail_react(register_login, create_channel_and_message):
    token = register_login['token']
    create_channel_and_message['channel_id']
    message_id = create_channel_and_message['message_id']
    react_id = 1

    # Calling message_react so that there will now be an active react_id on the message with ID message_id
    message_react(token, message_id, react_id)
    with pytest.raises(InputError):
        message_react(token, message_id, react_id)

''' Success Cases '''
def test_successful_react(register_login, create_channel_and_message):
    token = register_login['token']
    create_channel_and_message['channel_id']
    message_id = create_channel_and_message['message_id']

    react_id = 1
    message_react(token, message_id, react_id)
    check_react_id = create_channel_and_message['reacts']
    assert check_react_id[0]['react_id'] == 1

def test_successful_react_same_message_twice(register_login, create_channel_and_message):
    token = register_login['token']
    channel_id = create_channel_and_message['channel_id']
    message_id = create_channel_and_message['message_id']

    react_id = 1
    message_react(token, message_id, react_id)
    check_react_id = create_channel_and_message['reacts']
    assert check_react_id[0]['react_id'] == 1

    # Creating the second user, making them join the channel, create a message and react to it.
    auth_register("user2@email.com", "password2", "Richard2", "Shen2")
    user2 = auth_login("user2@email.com", "password2")
    user2_token = user2['token']
    channel_join(user2_token, channel_id)

    message_react(user2_token, message_id, react_id)
    check_react_id2 = channel_messages(user2_token, channel_id, 0)['messages']
    check_react_id2 = check_react_id2[0]['reacts'] 
    assert check_react_id2[0]['u_ids'] == [0, 1]

def test_successful_react_two_messages(register_login, create_channel_and_message):
    token = register_login['token']
    channel_id = create_channel_and_message['channel_id']
    message_id = create_channel_and_message['message_id']
    message_id2 = message_send(token, channel_id, "Message 2")['message_id']
    
    # Checking if the first message is reacted to by the user
    react_id = 1
    message_react(token, message_id, react_id)
    check_react_id = channel_messages(token, channel_id, 0)['messages'][0]
    check_react_id = check_react_id['reacts'] 
    assert check_react_id[0]['react_id'] == 1
    
    # Checking if the second message is reacted to by the user
    message_react(token, message_id2, react_id)
    check_react_id2 = channel_messages(token, channel_id, 0)['messages'][1]
    check_react_id2 = check_react_id2['reacts'] 
    assert check_react_id2[0]['react_id'] == 1
