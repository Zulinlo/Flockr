'''
channel_leave_test.py

Fixtures:
    register_new_user: registers a user and logs that user in

Test Modules:
    test_channel_leave_owner: tests success case where token and channel_id are valid and leaver is owner
    test_channel_leave_member: tests success case where token and channel_id are valid and leaver is non_owner
    test_user_already_in_channel: tests when user trying to join is already in channel
    test_test_invalid_channel_id: tests when channel_id is a negative number             
    test_private_channel: tests when channel is private and user is not an owner 
    test_second_user_added: tests to see if second user can be added after first user is added.
'''
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import pytest
from implement.other      import clear
from error      import InputError, AccessError
from implement.channels   import channels_create
from implement.auth       import auth_register, auth_login
from implement.channel    import channel_join, channel_leave, channel_details
from helper     import token_hash

@pytest.fixture
def register_new_user():
    clear()
    auth_register("test@gmail.com", "password", "Wilson", "Doe")
    user = auth_login("test@gmail.com", "password")
    return user

# Success Case
def test_channel_leave_owner(register_new_user):

    # Create the user
    new_user = register_new_user
    token = new_user['token']
    u_id = new_user['u_id']

    # Create the channel
    public = True
    channels_create(token, "Test Channel 2", public) 
    test_channel = channels_create(token, "Test Channel", public)
    c_id = test_channel['channel_id']
    in_channel = True

    # Create a new user who joins the channel
    auth_register("test@gmail2.com", "password1", "Bilson", "Doe")
    user2 = auth_login("test@gmail2.com", "password1")
    token2 = user2['token']
    channel_join(token2, c_id)
    
    # 1st member leaves, check if they are in the channel
    channel_leave(token, c_id)
    member_check = channel_details(token2, c_id)
    in_channel = u_id in member_check['all_members']
    in_owner = u_id in member_check['owner_members']
    
    assert in_channel == False
    assert in_owner == False

def test_channel_leave_member(register_new_user):

    # Create the user
    new_user = register_new_user
    token = new_user['token']

    # Create the channel
    public = True
    channels_create(token, "Test Channel 2", public) 
    test_channel = channels_create(token, "Test Channel", public)
    c_id = test_channel['channel_id']
    in_channel = True

    # Create a new user who joins the channel
    auth_register("test@gmail2.com", "password1", "Bilson", "Doe")
    user2 = auth_login("test@gmail2.com", "password1")
    token2 = user2['token']
    channel_join(token2, c_id)
    
    # 2nd member leaves, check if they are in the channel
    channel_leave(token2, c_id)
    member_check = channel_details(token, c_id)
    in_channel = user2['u_id'] in member_check['all_members']
    
    assert in_channel == False
# Fail Cases

# Assumption: Channels increment from 0 onwards. Therefore any negative values for c_id are invalid
def test_channel_leave_invalid_channel(register_new_user):
    new_user = register_new_user

    channels_create(new_user['token'], "Test Channel 1", True)

    with pytest.raises(InputError):
        channel_leave(new_user['token'], 4)

# User cannot leave channel when they haven't joined it
def test_channel_leave_unauthorised(register_new_user):
    new_user = register_new_user
    token = new_user['token']
    public = True
    test_channel = channels_create(token, "Test Channel", public)
    c_id = test_channel['channel_id']

    auth_register("test@gmail2.com", "password1", "Bilson", "Doe")
    user2 = auth_login("test@gmail2.com", "password1")

    with pytest.raises(AccessError):
        channel_leave(user2['token'], c_id)

# Access Error due to invalid token
def test_invalid_token(register_new_user):
    new_user = register_new_user
    token = new_user['token']

    public = True
    c_id = channels_create(token, "Test Channel", public)  
    with pytest.raises(AccessError):
        channel_leave(token_hash(1), c_id)
