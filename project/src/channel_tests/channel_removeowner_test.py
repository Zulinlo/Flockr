'''
channel_removeowner_test.py

Fixtures:
    channel_with_2_owners: creates channel and adds two users as owners

Test Modules:
    test_invalid_token: tests when token doesn't match expected user token
    test_invalid_channel_id: tests when channel_id is a negative number
    test_ivalid_u_id: tests when u_id is a negative number                                               
    test_invalid_owner_remove_1: tests when user trying to remove is not an owner                                                                                                                                                  
    test_invalid_owner_remove_2: tests when user trying to remove is not owner of the flockr or of the channel
    test_remove_owner_success: test success case where owner removes user from existing channel
'''

import pytest
from implement.other          import clear
from error          import InputError, AccessError
from implement.auth           import auth_register, auth_login
from implement.channel        import channel_removeowner, channel_addowner, channel_join, channel_details
from implement.channels       import channels_create
from helper         import token_hash

@pytest.fixture
def channel_with_2_owners():
    clear()

    # The first user is automatically an owner
    auth_register("owner@email.com", "password", "First", "Last")
    token_1 = auth_login("owner@email.com", "password")
    public = True

    # Create user and channel to be ignored but to pass authorised user
    auth_register("ignoreme@email.com", "password", "John", "Doe")
    ignore_me = auth_login("ignoreme@email.com", "password")
    channels_create(ignore_me['token'], "Ignore Me", public)

    c_id = channels_create(token_1['token'], "Channel", public)

    # The second user is made an owner for test purposes
    auth_register("owner2@email.com", "password2", "First2", "Last2")
    token_2 = auth_login("owner2@email.com", "password2")
    channel_join(token_2['token'], c_id['channel_id'])
    channel_addowner(token_1['token'], c_id['channel_id'], token_2['u_id'])
    
    return {
        'token_1': token_1, 
        'c_id': c_id, 
        'token_2': token_2
    }

# AccessError: token is invalid
def test_invalid_token(channel_with_2_owners):
    owner = channel_with_2_owners
    
    with pytest.raises(AccessError):
        channel_removeowner(token_hash(1), owner['c_id']['channel_id'], owner['token_2']['u_id'])

# InputError: channel_id does not refer to a valid channel.
def test_invalid_channel_id(channel_with_2_owners):
    owner = channel_with_2_owners
    invalid_c_id = -1
    with pytest.raises(InputError):
        channel_removeowner(owner['token_1']['token'], invalid_c_id, owner['token_2']['u_id'])

# InputError: u_id does not refer to a valid user
def test_ivalid_u_id(channel_with_2_owners):
    owner = channel_with_2_owners
    invalid_u_id = -1
    with pytest.raises(InputError):
        channel_removeowner(owner['token_1']['token'], owner['c_id']['channel_id'], invalid_u_id)

# InputError: User that is being removed with user id u_id 
#             is not an owner of the channel
def test_invalid_owner_remove_1(channel_with_2_owners):
    owner = channel_with_2_owners
    auth_register("not_owner@email.com", "password", "First", "Last")
    not_owner = auth_login("not_owner@email.com", "password")
    channel_join(not_owner['token'], owner['c_id']['channel_id'])
    with pytest.raises(InputError):
        channel_removeowner(owner['token_1']['token'], owner['c_id']['channel_id'], not_owner['u_id'])

# # AccessError: The user who wants to remove an owner is not 
# #              an owner of the flockr, or an owner of this channel
def test_invalid_owner_remove_2(channel_with_2_owners):
    owner = channel_with_2_owners
    auth_register("not_owner@email.com", "password", "First", "Last")
    not_owner = auth_login("not_owner@email.com", "password")
    channel_join(not_owner['token'], owner['c_id']['channel_id'])
    with pytest.raises(AccessError):
        channel_removeowner(not_owner['token'], owner['c_id']['channel_id'], owner['token_2']['u_id'])

def test_remove_owner_success(channel_with_2_owners):
    owner = channel_with_2_owners
    original_channel = channel_details(owner['token_1']['token'], owner['c_id']['channel_id'])

    assert len(original_channel['owner_members']) == 2
    assert original_channel['owner_members'][0]['u_id'] == 0
    assert original_channel['owner_members'][1]['u_id'] == 2

    channel_removeowner(owner['token_1']['token'], owner['c_id']['channel_id'], owner['token_2']['u_id'])
    updated_channel = channel_details(owner['token_1']['token'], owner['c_id']['channel_id'])

    assert len(updated_channel['owner_members']) == 1
    assert updated_channel['owner_members'][0]['u_id'] == 0

def test_flockr_owner():
    clear()

    # Register and login the global owner
    auth_register("flockr@owner.com", "password", "First", "Last")
    flockr_owner = auth_login("flockr@owner.com", "password")

    # Register and login 2 other users
    auth_register("owner1@email.com", "password", "First", "Last")
    owner_1 = auth_login("owner1@email.com", "password")

    auth_register("owner2@email.com", "password", "First", "Last")
    owner_2 = auth_login("owner2@email.com", "password")

    # Create a channel for owner_1
    public = True
    owner_1_c_id = channels_create(owner_1['token'], "Channel", public)['channel_id']
    channel_join(owner_2['token'], owner_1_c_id)

    # Make owner_2 actually an owner
    channel_addowner(owner_1['token'], owner_1_c_id, owner_2['u_id'])

    # The flockr_owner removes owner_2 as an owner 
    channel_removeowner(flockr_owner['token'], owner_1_c_id, owner_2['u_id'])

    details = channel_details(owner_1['token'], owner_1_c_id)
    assert len(details['owner_members']) == 1
    assert details['owner_members'][0]['u_id'] == 1
    
