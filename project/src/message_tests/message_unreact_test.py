'''
message_unreact_test.py

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
from error          import InputError
from implement.other          import clear
from implement.auth           import auth_register, auth_login
from implement.channels       import channels_create
from implement.channel        import channel_join, channel_details, channel_messages
from implement.message        import message_send, message_react, message_unreact

@pytest.fixture
def register_login():
    # Using the clear function in the register_login fixture so it won't have to be called after
    clear()
    # registers and logs in a user
    auth_register("user@email.com", "password", "Angus", "Doe")
    user = auth_login("user@email.com", "password")
    return {
        "u_id": user["u_id"],
        "token": user["token"]
    }

@pytest.fixture
def create_channel_and_message_react(register_login):
    # register a user and log them in so they have a token.
    user = register_login
    token = user['token']
    is_public = True
    # creating public channel
    channel_id = channels_create(token, "Channel", is_public)
    # send a message and react it with react_id 1
    message_example = 'hello anto'
    message = message_send(token, channel_id['channel_id'], message_example)
    message_id = message['message_id']
    react_id = 1
    message_react(token, message_id, react_id)
    message_details = channel_messages(token, channel_id['channel_id'], 0)['messages']

    return {
        'channel_id': channel_id['channel_id'],
        'message_id': message['message_id'],
        'reacts': message_details[0]['reacts']
    }

''' Success Cases '''
def test_successful_unreact(register_login, create_channel_and_message_react):
    token = register_login['token']
    message_id = create_channel_and_message_react['message_id']
    channel_id = create_channel_and_message_react['channel_id']
    # u_id of 0 should be in u_ids list
    message_details = channel_messages(token, channel_id, 0)['messages']
    check_react_uids = message_details[0]['reacts']
    assert check_react_uids[0]['u_ids'] == [0]

    react_id = 1
    message_unreact(token, message_id, react_id)
    # u_id of 0 should be removed from u_id list.
    message_details = channel_messages(token, channel_id, 0)['messages']
    check_react_uids = message_details[0]['reacts']
    assert check_react_uids[0]['u_ids'] == []

def test_successful_unreact_two_reacts(register_login, create_channel_and_message_react):
    token = register_login['token']
    message_id = create_channel_and_message_react['message_id']
    channel_id = create_channel_and_message_react['channel_id']
    # u_id of 0 should be in u_ids list
    message_details = channel_messages(token, channel_id, 0)['messages']
    check_react_uids = message_details[0]['reacts']
    assert check_react_uids[0]['u_ids'] == [0]

    react_id = 1
    message_unreact(token, message_id, react_id)
    # u_id of 0 should be removed from u_id list.
    message_details = channel_messages(token, channel_id, 0)['messages']
    check_react_uids = message_details[0]['reacts']
    assert check_react_uids[0]['u_ids'] == []
    
    message_example = 'hello again anto'
    message = message_send(token, 0, message_example)
    message_id = message['message_id']
    react_id = 1
    message_react(token, message_id, react_id)
    message_details = channel_messages(token, channel_id, 0)['messages']
    check_react_uids = message_details[1]['reacts']
    assert check_react_uids[0]['u_ids'] == [0]

    react_id = 1
    message_unreact(token, message_id, react_id)
    # u_id of 0 should be removed from u_id list.
    message_details = channel_messages(token, channel_id, 0)['messages']
    check_react_uids = message_details[1]['reacts']
    assert check_react_uids[0]['u_ids'] == []

''' Fail Cases '''
def test_invalid_messageid(register_login, create_channel_and_message_react):
    token = register_login['token']
    invalid_message_id = -1
    react_id = 1
    with pytest.raises(InputError):
        message_unreact(token, invalid_message_id, react_id)
    
def test_user_not_in_channel(register_login, create_channel_and_message_react):
    message_id = create_channel_and_message_react['message_id']
    # Creating a second channel which will not have the messages, and make a new user 
    auth_register("user2@email.com", "password2", "angus2", "doe2")
    user2 = auth_login("user2@email.com", "password2")
    user2_token = user2['token']
    
    react_id = 1
    with pytest.raises(InputError):
        message_unreact(user2_token, message_id, react_id)
    
def test_invalid_react_id(register_login, create_channel_and_message_react):
    token = register_login['token']
    message_id = create_channel_and_message_react['message_id']
    channel_id = create_channel_and_message_react['channel_id']
    # u_id of 0 should be in u_ids list
    message_details = channel_messages(token, channel_id, 0)['messages']
    check_react_uids = message_details[0]['reacts']
    assert check_react_uids[0]['u_ids'] == [0]

    react_id = -1
    with pytest.raises(InputError):
        message_unreact(token, message_id, react_id)

def test_unreact_noreacts(register_login):
    user = register_login
    token = user['token']
    is_public = True
    # creating public channel
    channel_id = channels_create(token, "Channel", is_public)
    # send a message but no reacts
    message_example = 'hello anto'
    message = message_send(token, channel_id['channel_id'], message_example)
    message_id = message['message_id']
    react_id = 1
    with pytest.raises(InputError):
        message_unreact(token, message_id, react_id)