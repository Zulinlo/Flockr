'''
message_unpin_test.py

Assumptions:
- Only the owner of the flockr (global owner) or the owner of the channel
is authorised to unpin messages.
- Members of the channel are not authorised to unpin messages in a channel 
that they are in.

Fixtures:
    channel_user_message_pin: A user is registered, logged in and owns a channel which contains a message which is pinned
    
Test Modules:
    - Failure Cases:
    test_invalid_token: Raises an AccessError for an invalid token.
    test_invalid_message_id: Raises an InputError if the message_id is not a valid message.
    test_invalid_already_unpinned: Raises an InputError if Message with ID message_id is already unpinned.
    test_invalid_external_user_unpin: Raises an AccessError if the authorised user is not a member of the channel 
                            that the message is within
    test_invalid_unauthorised_user_unpin: Raises an AccessError if the authorised user is not an owner or flockr owner.

    - Success Cases:
    test_valid_message_unpin_owner: valid case when the owner of the channel unpins a pinned message
    test_valid_message_unpin_flockr_owner: valid case when the flockr owner unpins a pinned message
'''
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import pytest
from error          import InputError, AccessError
from implement.other          import clear, search
from implement.auth           import auth_register, auth_login
from implement.channels       import channels_create
from implement.channel        import channel_join, channel_details
from helper         import token_hash
from implement.message        import message_send, message_pin, message_unpin

@pytest.fixture
def channel_user_message_pin():
    clear()
    flockr_owner = auth_register("flockrowner@email.com", "password", "John", "Doe")

    auth_register("owner@email.com", "password", "Firstname", "Lastname")
    owner = auth_login("owner@email.com", "password")

    public = True
    c_id = channels_create(owner['token'], "Channel", public)
    message = message_send(owner['token'], c_id['channel_id'], "Test Message 1")
    message_pin(owner['token'], message['message_id'])

    return {
        'u_id': owner['u_id'], 
        'token': owner['token'], 
        'flockr_owner_token': flockr_owner['token'],
        'c_id': c_id['channel_id'],
        'message_id': message['message_id']
    }

'''Invalid Cases'''
#AccessError: Invalid Token
def test_invalid_token(channel_user_message_pin):
    owner = channel_user_message_pin

    invalid_token = token_hash(2)
    with pytest.raises(AccessError):
        message_unpin(invalid_token, owner['message_id'])

# InputError: message_id is not a valid message
def test_invalid_message_id(channel_user_message_pin):
    owner = channel_user_message_pin

    invalid_m_id = -1
    with pytest.raises(InputError):
        message_unpin(owner['token'], invalid_m_id)

# InputError: Message with ID message_id is already unpinned
def test_invalid_already_unpinned(channel_user_message_pin):
    owner = channel_user_message_pin

    unpinned_message = message_send(owner['token'], owner['c_id'], "Unpinned message") 

    # Unpin the same message
    with pytest.raises(InputError):
        message_unpin(owner['token'], unpinned_message['message_id'])

# AccessError: Authorised user is not a member of the channel 
#              that the message is within
def test_invalid_external_user_unpin(channel_user_message_pin):
    owner = channel_user_message_pin

    auth_register("member@email.com", "password", "Firstname", "Lastname")
    member = auth_login("member@email.com", "password")
    
    owner_channel = channel_details(owner['token'], owner['c_id'])
    assert member['u_id'] not in owner_channel['all_members']

    with pytest.raises(AccessError):
        message_unpin(member['token'], owner['message_id'])

# AccessError: Authorised user is not an owner
def test_unauthorised_user_pin(channel_user_message_pin):
    owner = channel_user_message_pin

    auth_register("member@email.com", "password", "Firstname", "Lastname")
    member = auth_login("member@email.com", "password")
    channel_join(member['token'], owner['c_id'])

    owner_channel = channel_details(owner['token'], owner['c_id'])
    assert member['u_id'] not in owner_channel['all_members']

    with pytest.raises(AccessError):
        message_unpin(member['token'], owner['message_id'])

'''Success Cases'''
def test_valid_message_unpin_owner(channel_user_message_pin):
    owner = channel_user_message_pin

    message = search(owner['token'], "Test Message 1")['messages']
    assert message[0]['is_pinned']
    
    message_unpin(owner['token'], owner['message_id'])

    message = search(owner['token'], "Test Message 1")['messages']
    assert not message[0]['is_pinned']

def test_valid_message_unpin_flockr_owner(channel_user_message_pin):
    owner = channel_user_message_pin

    message = search(owner['token'], "Test Message 1")['messages']
    assert message[0]['is_pinned']
    
    message_unpin(owner['flockr_owner_token'], owner['message_id'])

    message = search(owner['token'], "Test Message 1")['messages']
    assert not message[0]['is_pinned']
