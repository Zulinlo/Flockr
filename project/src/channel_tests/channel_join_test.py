'''
channel_join_test.py

Fixtures:
    register_user: registers a user and logs that user in

Test Modules:
    test_invalid_token: tests when token is invalid
    test_user_already_in_channel: tests when user trying to join is already in channel
    test_test_invalid_channel_id: tests when channel_id is a negative number                                                  
    test_private_channel: tests when channel is private and user is not an owner                                                                                                                                                     
    test_second_user_added: tests to see if second user can be added after first user is added.
'''
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import pytest
from error          import InputError, AccessError
from implement.other          import clear
from implement.auth import auth_register, auth_login
from implement.channels       import channels_create
from implement.channel        import channel_join, channel_details
from helper         import token_hash

@pytest.fixture
def register_login_user():
    clear()
    auth_register("user@email.com", "password", "First", "Last")
    token = auth_login("user@email.com", "password")
    return token

def test_invalid_token(register_login_user):
    token = register_login_user
    public = True
    c_id = channels_create(token['token'], "Channel", public)
    with pytest.raises(AccessError):
        channel_join(token_hash(1), c_id['channel_id'])

def test_user_already_in_channel(register_login_user):
    token = register_login_user
    public = True
    c_id = channels_create(token['token'], "Channel", public)
    with pytest.raises(AccessError):
        channel_join(token['token'], c_id['channel_id'])

# InputError: channel_id is not a valid channel
def test_invalid_channel_id(register_login_user):
    token = register_login_user
    invalid_c_id = -1
    with pytest.raises(InputError):
        channel_join(token['token'], invalid_c_id)

# AccessError: channel_id refers to a channel that is private 
# (when the authorised user is not an admin)
def test_private_channel(register_login_user):
    owner = register_login_user 

    # Register and login a new user who plans to join the channel
    auth_register("member@email.com", "password", "First", "Last")
    member = auth_login("member@email.com", "password")

    private = False
    c_id = channels_create(owner['token'], "Channel", private)
    with pytest.raises(AccessError):
        channel_join(member['token'], c_id['channel_id'])

# Check that a second member can be added to the channel
def test_second_user_added(register_login_user):
    token_1 = register_login_user
    auth_register("user2@email.com", "password", "First", "Last")
    token_2 = auth_login("user2@email.com", "password")
    public = True
    c_id = channels_create(token_1['token'], "Channel", public)
    channel_join(token_2['token'], c_id['channel_id'])
    
    details = channel_details(token_1['token'], c_id['channel_id'])
    assert details['all_members'] == [
            {'u_id': 0, 'name_first': 'First', 'name_last': 'Last', 'profile_img_url': 'default.jpg'}, 
            {'u_id': 1, 'name_first': 'First', 'name_last': 'Last', 'profile_img_url': 'default.jpg'}
    ]

def test_flockr_owner(register_login_user):
    # Keep the flockr owner seperate from channel owners
    flockr_owner = register_login_user

    # Register and login another user who is an owner
    auth_register("owner@email.com", "password", "First", "Last")
    owner = auth_login("owner@email.com", "password")

    # This owner then creates a channel
    private = False
    owner_c_id = channels_create(owner['token'], "Owner Channel", private)['channel_id']

    # Flockr owner joins a channel
    channel_join(flockr_owner['token'], owner_c_id)

    details = channel_details(owner['token'], owner_c_id)

    assert details['all_members'] == [
            {'u_id': 1, 'name_first': 'First', 'name_last': 'Last', 'profile_img_url': 'default.jpg'}, 
            {'u_id': 0, 'name_first': 'First', 'name_last': 'Last', 'profile_img_url': 'default.jpg'}
    ]
