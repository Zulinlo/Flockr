"""
channels_list_test.py

Fixtures:
    register_login_create_channel: creates a user, logs in, creates a channel with that user
    register_login_user2: creates a user2, logs in

Test Modules:
    test_valid_token: creates one channel under a user, runs list and makes sure it retrieves only that one channel
    test_list_multiple_and_only_user: creates 2 channels under user, and another one under user2 and makes sures to only retrieve the 2 channels
    test_invalid_token: given an invalid token expect an AccessError
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import pytest
from implement.other          import clear
from error          import AccessError
from implement.auth           import auth_register, auth_login
from implement.channels       import channels_create, channels_list
from helper         import token_hash

@pytest.fixture
def register_login_create_channel():
    clear()
    # register and login a user
    auth_register("test@email.com", "password", "Angus", "Doe")
    login = auth_login("test@email.com", "password")
    token = login['token']

    # create channel using that user
    channels_create(token, "test channel", True)

    return token

@pytest.fixture
def register_login_user2():
    # register
    auth_register("test2@email.com", "password", "Bingus", "Doe")
    login = auth_login("test2@email.com", "password")
    token = login['token']

    return token

def test_unretrieved_channel(register_login_create_channel, register_login_user2):
    token = register_login_create_channel
    token2 = register_login_user2
   
    # create channel which should not be retrieved
    channels_create(token2, "unretrieved channel", True)

    result = channels_list(token)

    assert result == {'channels': [
        {
            'channel_id': 0,
            'name': 'test channel',
            'owner_members': [0],
            'all_members': [0],
            'is_public': True,
            'time_finish': None,
            'messages': [],
        }
    ]}

def test_list_multiple_and_only_user(register_login_create_channel, register_login_user2):
    token = register_login_create_channel
    channels_create(token, "test2 channel", True)

    token2 = register_login_user2
    channels_create(token2, "unretrieved channel", True)

    result = channels_list(token)
    
    assert result == {'channels': [
        {
            'channel_id': 0,
            'name': 'test channel',
            'owner_members': [0],
            'all_members': [0],
            'is_public': True,
            'time_finish': None,
            'messages': [],

        },
        {
            'channel_id': 1,
            'name': 'test2 channel',
            'owner_members': [0],
            'all_members': [0],
            'is_public': True,
            'time_finish': None,
            'messages': [],

        }
    ]}

def test_invalid_token(register_login_create_channel):
    # should throw error since token will be invalid
    with pytest.raises(AccessError):
        channels_list(token_hash(3))
