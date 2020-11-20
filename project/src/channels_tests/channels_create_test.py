"""
channels_create_test.py

Fixtures:
    register_login: creates a user and logs into that user

Helper Modules:
    check_channel_created: verify that the channel has been created

Test Modules:
    test_invalid_token: tests for invalid token
    test_invalid_name_edge_case: tests when channel_name is > 20
    test_invalid_name_empty: tests when name is empty
    test_valid_name_and_token: tests for a valid channel creation
    test_invalid_is_public: tests when is_public is invalid
    test_valid_is_public_true: tests when is_public = True
    test_valid_is_public_false: tests when is_public = False
    test_valid_creator_is_owner: tests if the channel created has the right owner
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import pytest
from error      import InputError, AccessError
from implement.other      import clear
from implement.auth       import auth_register, auth_login
from implement.channels   import channels_create, channels_listall
from helper     import token_hash

@pytest.fixture
def register_login():
    clear()
    auth_register("example@gmail.com", "password", "Sam", "Wu")
    user = auth_login("example@gmail.com", "password")

    return user

def check_channel_created(token, c_id):
    all_channels = channels_listall(token)

    channel_exists = False
    for channel in all_channels['channels']:
        if c_id == channel['channel_id']:
            channel_exists = True

    return channel_exists

def test_invalid_token(register_login):
    channel_name = 'ChannelisValid'
    is_public = True

    with pytest.raises(AccessError):
        channels_create(token_hash(1), channel_name, is_public)

def test_invalid_name_edge_case(register_login):
    user = register_login
    channel_name = 'ChannelIsOver20EdgeCase'
    is_public = True

    # Expect to fail because channel_name is > 20 characters
    with pytest.raises(InputError):
        channels_create(user['token'], channel_name, is_public)

def test_invalid_name_empty(register_login):
    user = register_login
    channel_name = ''
    is_public = True

    with pytest.raises(InputError):
        channels_create(user['token'], channel_name, is_public)

def test_valid_name_and_token(register_login):
    user = register_login
    channel_name = 'V4Lid:/42_|}%&*'
    is_public = True

    # Input a dummy channel
    c_id = channels_create(user['token'], channel_name, is_public)

    # Check if inserted
    # Scan through all channels to see if channel was created
    channel_exists = check_channel_created(user['token'], c_id['channel_id'])

    assert channel_exists

def test_invalid_is_public(register_login):
    user = register_login
    channel_name = 'ValidName1'
    is_public = 'NotBoolean!'

    # Invalid when is_public is not boolean
    with pytest.raises(InputError):
        channels_create(user['token'], channel_name, is_public)

def test_valid_is_public_true(register_login):
    user = register_login
    channel_name = 'ChannelValidUnder20'
    is_public = True

    # Input a dummy channel
    c_id = channels_create(user['token'], channel_name, is_public)

    # Check if inserted
    # Scan through all channels to see if channel was created
    channel_exists = check_channel_created(user['token'], c_id['channel_id'])

    assert channel_exists

def test_valid_is_public_false(register_login):
    user = register_login
    channel_name = 'ChannelValidUnder20'
    is_public = False

    # Input a dummy channel
    c_id = channels_create(user['token'], channel_name, is_public)

    # Check if inserted
    # Scan through all channels to see if channel was created
    channel_exists = check_channel_created(user['token'], c_id['channel_id'])

    assert channel_exists

def test_invalid_creator_is_owner(register_login):
    user = register_login
    channel_name = 'ChannelValidUnder20'
    is_public = True

    c_id = channels_create(user['token'], channel_name, is_public)

    # Check if inserted
    # Scan through all channels to see if owner exists
    all_channels = channels_listall(user['token'])

    owner_exists = False
    for channel in all_channels['channels']:
        if c_id['channel_id'] == channel['channel_id']:
            if user['u_id'] in channel['owner_members']:
                owner_exists = True

    assert owner_exists
