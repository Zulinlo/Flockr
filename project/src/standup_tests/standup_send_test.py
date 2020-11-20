"""
standup_send_test.py

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
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import pytest
from error      import InputError, AccessError
from implement.other      import clear
from implement.auth       import auth_register, auth_login
from implement.channels   import channels_create
from implement.channel    import channel_details, channel_messages, channel_join
from implement.message    import message_send
from implement.user       import user_profile
from time       import sleep
from helper     import token_hash
from implement.standup    import standup_start, standup_active, standup_send

@pytest.fixture
def channel_with_user():
    clear()
    auth_register("owner@email.com", "password", "Firstname", "Lastname")
    user = auth_login("owner@email.com", "password")
    public = True
    c_id = channels_create(user['token'], "Channel", public)

    return {
        'u_id': user['u_id'], 
        'token': user['token'], 
        'c_id': c_id['channel_id'],
    }

@pytest.fixture
def standup(channel_with_user):
    owner = channel_with_user
    standup_length = 1
    time = standup_start(owner['token'], owner['c_id'], standup_length)
    active = standup_active(owner['token'], owner['c_id'])

    return {
        'is_active': active,
        'time_finish': time,
    }

'''Invalid Cases'''
# AccessError: token was invalid
def test_invalid_token(channel_with_user, standup):
    sender = channel_with_user
    assert standup['is_active']
    invalid_token = token_hash(-1)
    with pytest.raises(AccessError):
        standup_send(invalid_token, sender['c_id'], "Invalid Token")

# InputError: Channel ID is not a valid channel
def test_invalid_c_id(channel_with_user, standup):
    assert standup['is_active']
    sender = channel_with_user

    invalid_c_id = -1
    with pytest.raises(InputError):
        standup_send(sender['token'], invalid_c_id, "Invalid Channel ID")

# InputError: Message is more than 1000 characters
def test_invalid_message_1001(channel_with_user, standup):
    assert standup['is_active']
    sender = channel_with_user

    invalid_message = "*" * 1001
    assert len(invalid_message) == 1001

    with pytest.raises(InputError):
        standup_send(sender['token'], sender['c_id'], invalid_message)

# InputError: An active standup is not currently running in this channel
def test_inactive_standup(channel_with_user):
    sender = channel_with_user

    standup = standup_active(sender['token'], sender['c_id'])
    assert not standup['is_active']

    with pytest.raises(InputError):
        standup_send(sender['token'], sender['c_id'], "Test Message")

# AccessError: Authorised user is not a member of the channel 
#              that the message is within
def test_external_user(channel_with_user, standup):
    assert standup['is_active']
    sender = channel_with_user

    auth_register("member@email.com", "password", "Firstname", "Lastname")
    member = auth_login("member@email.com", "password")
    
    sender_channel = channel_details(sender['token'], sender['c_id'])
    assert member['u_id'] not in sender_channel['all_members']

    with pytest.raises(AccessError):
        standup_send(member['token'], sender['c_id'], "Test Message")

'''Success Cases'''
def test_standup_send_multiple(channel_with_user, standup):
    assert standup['is_active']
    sender = channel_with_user

    standup_send(sender['token'], sender['c_id'], "Test Message 1")
    standup_send(sender['token'], sender['c_id'], "Test Message 2")

    until_standup_finishes = 2 # seconds
    sleep(until_standup_finishes)

    messages = channel_messages(sender['token'], sender['c_id'], 0)['messages']
    handle_str = user_profile(sender['token'], sender['u_id'])['user']['handle_str']
    standup_messages = f"{handle_str}: Test Message 1\n" + f"{handle_str}: Test Message 2"

    assert messages[0]['message'] == standup_messages

def test_standup_send_1000(channel_with_user, standup):
    assert standup['is_active']
    sender = channel_with_user
    valid_message = "*" * 1000

    standup_send(sender['token'], sender['c_id'], valid_message)

    until_standup_finishes = 2 # seconds
    sleep(until_standup_finishes)

    messages = channel_messages(sender['token'], sender['c_id'], 0)['messages']
    handle_str = user_profile(sender['token'], sender['u_id'])['user']['handle_str']

    assert messages[0]['message'] == f"{handle_str}: {valid_message}"

def test_standup_send_member(channel_with_user, standup):
    assert standup['is_active']
    owner = channel_with_user
    
    # Login and register another user who will send the message
    auth_register('member@email.com', 'password', 'name_first', 'name_last')
    member = auth_login('member@email.com', 'password')
    channel_join(member['token'], owner['c_id'])

    standup_send(member['token'], owner['c_id'], "Member Message")

    until_standup_finishes = 2 # seconds
    sleep(until_standup_finishes)

    messages = channel_messages(member['token'], owner['c_id'], 0)['messages']
    handle_str = user_profile(member['token'], member['u_id'])['user']['handle_str']

    assert messages[0]['message'] == f"{handle_str}: Member Message"
