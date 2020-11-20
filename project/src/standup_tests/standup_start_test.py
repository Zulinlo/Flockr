"""
standup_start_test.py

Fixtures:
    register_3_users_channel: registers 2 users and creates a channel which the first user is the owner of and the second user is a member and third user is not a part of, returns c_id and user_id and tokens

Test Modules:
    - Failure Cases:
    test_invalid_token: tests for invalid token
    test_invalid_channel: test for if channel_id is not created
    test_invalid_active_standup: test for if there is already an active standup
    
    - Success Cases:
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

@pytest.fixture
def register_2_users_channel():
    clear()
    
    # Create a dummy channel for coverage where code loops through channels
    owner = auth_register("creator@gmail.com", "password", "Angus", "Doe")
    channels_create(owner['token'], "Dummy Channel", True)

    # Create a user who is flockr owner and is creating the channel
    c_id = channels_create(owner['token'], "Channel", True)

    member = auth_register("member@gmail.com", "password", "Bungus", "Two")
    channel_join(member['token'], c_id['channel_id'])

    return {
        'c_id': c_id['channel_id'], 
        'owner': owner, 
        'member': member, 
    }

'''Invalid Cases'''
def test_invalid_token(register_2_users_channel):
    channel = register_2_users_channel
    invalid_token = token_hash(-1)
    standup_length = 1
    with pytest.raises(AccessError):
        standup_start(invalid_token, channel['c_id'], standup_length)

def test_invalid_channel(register_2_users_channel):
    channel = register_2_users_channel
    invalid_c_id = -1
    standup_length = 1
    with pytest.raises(InputError):
        standup_start(channel['owner']['token'], invalid_c_id, standup_length)

def test_invalid_active_standup(register_2_users_channel):
    channel = register_2_users_channel
    standup_length = 1
    # Start the first standup
    time_finish = standup_start(channel['member']['token'], channel['c_id'], standup_length)['time_finish']
    
    result = standup_active(channel['member']['token'], channel['c_id'])
    assert result == {
        'is_active': True,
        'time_finish': time_finish
    }
    # Ensure that another standup cannot be started
    with pytest.raises(InputError):
       standup_start(channel['owner']['token'], channel['c_id'], standup_length) 

'''Success Cases'''
def test_valid_member(register_2_users_channel):
    channel = register_2_users_channel
    standup_length = 1
    standup_start(channel['member']['token'], channel['c_id'], standup_length)

    standup = standup_active(channel['member']['token'], channel['c_id'])
    assert standup['is_active']

def test_valid_owner(register_2_users_channel):
    channel = register_2_users_channel
    standup_length = 1
    standup_start(channel['owner']['token'], channel['c_id'], standup_length)

    standup = standup_active(channel['owner']['token'], channel['c_id'])

    assert standup['is_active']

