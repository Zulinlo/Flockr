"""
standup_active_test.py

Fixtures:
    register_login: registers a user and creates a channel which the first user is the owner of

Test Modules:
    test_invalid_token: tests for invalid token
    test_invalid_channel: test for if channel_id is not created
    test_invalid_active_standup: test for if there is already an active standup
    test_valid_member: when the user is apart of the valid channel and no active standup is currently running
    test_valid_owner: valid case for when the owner creates the standup
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import pytest
from error          import InputError, AccessError
from implement.other          import clear
from implement.auth           import auth_register, auth_login
from implement.channels       import channels_create
from implement.channel        import channel_join
from implement.standup        import standup_start, standup_active
from helper         import token_hash
from time           import sleep

@pytest.fixture
def register_login():
    clear()
    
    # Create a user who is flockr owner and is creating the channel
    auth_register("user@email.com", "password", "Richard", "Shen")
    user = auth_login("user@email.com", "password")
    is_public = True
    channel_id = channels_create(user['token'], "Channel", is_public)
    '''
    auth_register("user2@email.com", "password2", "Richard2", "Shen2")
    user2 = auth_login("user2@email.com", "password2")
    channel_join(user2['token'], channel_id['channel_id'])
    '''
    return {
        'token': user['token'],
        'channel_id': channel_id['channel_id'], 
    }

def test_invalid_token(register_login):
    channel_id = register_login['channel_id']
    invalid_token = token_hash(-1)

    with pytest.raises(AccessError):
        standup_active(invalid_token, channel_id)

def test_invalid_channel_id(register_login):
    token = register_login['token']
    invalid_channel_id = -1
    with pytest.raises(InputError):
        standup_active(token, invalid_channel_id)

def test_inactive_standup(register_login):
    token = register_login['token']
    channel_id = register_login['channel_id']
    result = standup_active(token, channel_id)
    assert result == {
        'is_active': False,
        'time_finish': None
    }

def test_2_standups(register_login):
    token = register_login['token']
    channel_id = register_login['channel_id']
    # Start the first standup
    time_finish = standup_start(token, channel_id, 1)['time_finish']
    result = standup_active(token, channel_id)

    assert result == {
        'is_active': True,
        'time_finish': time_finish
    }
    # Ensure the first standup finishes
    sleep(2)
    result = standup_active(token, channel_id)
    assert result == {
        'is_active': False,
        'time_finish': None
    }
    # Start the second standup
    time_finish = standup_start(token, channel_id, 1)['time_finish']
    result = standup_active(token, channel_id)

    assert result == {
        'is_active': True,
        'time_finish': time_finish
    }
    # Ensure the second standup finishes
    sleep(2)
    result = standup_active(token, channel_id)
    assert result == {
        'is_active': False,
        'time_finish': None
    }