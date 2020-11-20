'''
channel_addowner_test.py

Fixtures:
    register_login: registers a user and logs that user in

Test Modules:
    test_invalid_token: tests when token doesn't match users token
    test_invalid_channel_id: tests when channel_id doesn't exist
    test_invalid_u_id: tests when u_id doesn't refer to a valid user                                                                                                                                                                                    
    test_user_already_owner: tests when user to be owner is already an owner                                                                                                                                                          
    test_test_invalid_owner_add: tests when authorised user is not an owner, but is trying to make someone else an owner.                                                                                                                                                                           
    test_add_owner_success: tests success case where ownder adds a valid user.
'''
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import pytest
from error          import InputError, AccessError
from implement.other          import clear
from implement.auth import auth_register, auth_login
from implement.channels       import channels_create
from implement.channel        import channel_addowner, channel_invite, channel_details, channel_join
from helper         import token_hash

@pytest.fixture
def register_login():
    clear()
    auth_register("test@gmail.com", "password", "Richard", "Shen")
    token = auth_login("test@gmail.com", "password")
    return token

# Testing if the token is invalid or not, should raise AccessError
def test_invalid_token(register_login):
    token = register_login
    public = True
    c_id = channels_create(token['token'], "Channel", public)
    invalid_token = token_hash(1)
    with pytest.raises(AccessError):
        channel_addowner(invalid_token, c_id['channel_id'], token['u_id'])

# Testing if the channel_id is invalid or not, should raise InputError
def test_invalid_channel_id(register_login):
    token = register_login
    auth_register("test2@gmail.com", "password2", "Richard2", "Shen2")
    token2 = auth_login("test2@gmail.com", "password2")
    invalid_c_id = -1
    with pytest.raises(InputError):
        channel_addowner(token['token'], invalid_c_id, token2['u_id'])

# InputError: u_id does not refer to a valid user
def test_invalid_u_id(register_login):
    token = register_login
    public = True
    c_id = channels_create(token['token'], "Channel", public)
    invalid_u_id = -1
    with pytest.raises(InputError):
        channel_addowner(token['token'], c_id['channel_id'], invalid_u_id)

# Testing if the user is already an owner or not, should raise InputError
def test_user_already_owner(register_login):
    token = register_login
    public = True
    c_id = channels_create(token['token'], "Channel", public)
    with pytest.raises(InputError):
        channel_addowner(token['token'], c_id['channel_id'], token['u_id'])

# Authorised user is not an owner, but is trying to make someone else an owner.
def test_invalid_owner_add(register_login):
    # Register the first user who is the owner of the channel
    token = register_login
    public = True
    c_id = channels_create(token['token'], "Channel", public)
    # Create a second user
    auth_register("test2@gmail.com", "password2", "Richard2", "Shen2")
    token2 = auth_login("test2@gmail.com", "password2")
    # Create a third user
    auth_register("test3@gmail.com", "password3", "Richard3", "Shen3")
    token3 = auth_login("test3@gmail.com", "password3")
    # Make both new users join the channel
    channel_join(token2['token'], c_id['channel_id'])
    channel_join(token3['token'], c_id['channel_id'])
    details = channel_details(token['token'], c_id['channel_id'])
    assert details['all_members'][1]['u_id'] == 1
    # Should raise AccessError if the newly joined member tries to make the other member an owner
    with pytest.raises(AccessError):
        channel_addowner(token3['token'], c_id['channel_id'], token2['u_id'])

# Testing if the owner can add a member as an owner successfuly
def test_add_owner_success(register_login):
    token = register_login
    public = True

    # Create channel to be ignored but considered when testing
    auth_register("test2@gmail.com", "password", "ignore", "me")
    ignore_me = auth_login("test2@gmail.com", "password")
    channels_create(ignore_me['token'], "IgnoreMe", public)

    c_id = channels_create(token['token'], "Channel", public)

    auth_register("user2@email.com", "password", "First", "Last")
    token2 = auth_login("user2@email.com", "password")
    channel_join(token2['token'], c_id['channel_id'])
    details = channel_details(token['token'], c_id['channel_id'])

    assert len(details['owner_members']) == 1
    assert(details['owner_members'][0]['u_id']) == 0
    channel_addowner(token['token'], c_id['channel_id'], token2['u_id'])

    details = channel_details(token['token'], c_id['channel_id'])
    assert len(details['owner_members']) == 2
    assert details['owner_members'][1]['u_id'] == token2['u_id']

# Testing that the user is the flockr owner, not an owner of the channel
def test_is_flockr_owner(register_login):
    # Creating the flockr owner, which is the first user to be registered
    flockr_owner = register_login
    flockr_token = flockr_owner['token']
    # Creating a new user who will be the channel owner
    auth_register("owner@gmail.com", "ownerpassword", "ownerRichard", "ownerShen")
    owner = auth_login("owner@gmail.com", "ownerpassword")
    public = True
    c_id = channels_create(owner['token'], "Channel", public)
    # Creating a new user who will be just a member of the channel
    auth_register("member@gmail.com", "memberpassword", "memberRichard", "memberShen")
    member = auth_login("member@gmail.com", "memberpassword")
    channel_join(member['token'], c_id['channel_id'])
    # Making the member the owner via the permissions of the flockr owner
    channel_addowner(flockr_token, c_id['channel_id'], member['u_id'])
    details = channel_details(owner['token'], c_id['channel_id'])
    assert details['owner_members'][1]['u_id'] == member['u_id']
