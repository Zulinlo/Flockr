'''
channel_invite_test.py

Fixtures:
    register_and_login_user: registers a user and logs that user in

Test Modules:
    test_invalid_token: tests when token is invalid
    test_test_invalid_channel_id: tests when channel_id is a negative number   
    test_invalid_u_id: tests when u_id is a negative number                                                 
    test_invalid_reinvite: tests user invites user that has already been invited                                                                                                                                                     
    test_invite_success: tests success case where all inputs are valid
'''
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import pytest
from implement.other          import clear
from error          import InputError, AccessError
from implement.channel        import channel_invite, channel_details
from implement.auth import auth_register, auth_login
from implement.channels       import channels_create
from helper         import token_hash

@pytest.fixture
def register_and_login_user():
    clear()
    auth_register("test@email.com", "password", "First", "Last")
    token = auth_login("test@email.com", "password")
    return token

# AccessError: token passed in is invalid
def test_invalid_token(register_and_login_user):
    token = register_and_login_user
    private = False
    c_id = channels_create(token['token'], "Channel", private)
    invalid_token = token_hash(1)
    with pytest.raises(AccessError):
        channel_invite(invalid_token, c_id, token['u_id'])

# InputError: channel_id does not refer to a valid channel.
def test_invalid_channel_id(register_and_login_user):
    token = register_and_login_user
    invalid_c_id = -1
    with pytest.raises(InputError):
        channel_invite(token['token'], invalid_c_id, token['u_id'])

# InputError: u_id does not refer to a valid user
def test_invalid_u_id(register_and_login_user):
    token = register_and_login_user
    private = False
    c_id = channels_create(token['token'], "Channel", private)
    invalid_u_id = -1
    with pytest.raises(InputError):
        channel_invite(token['token'], c_id, invalid_u_id)

# Check that the user can't invite themselves
def test_invalid_reinvite(register_and_login_user):
    token = register_and_login_user
    private = False
    c_id = channels_create(token['token'], "Channel", private)
    with pytest.raises(AccessError):
        channel_invite(token['token'], c_id['channel_id'], token['u_id'])

# Check that a user who is in the channel can invite another
# user who is not in the channel
def test_invite_success(register_and_login_user):
    token_1 = register_and_login_user
    auth_register("test2@email.com", "password2", "First2", "Last2")
    token_2 = auth_login("test2@email.com", "password2")
    private = False
    c_id = channels_create(token_1['token'], 'User_1s Channel', private)
    channel_invite(token_1['token'], c_id['channel_id'], token_2['u_id'])

    details = channel_details(token_1['token'], c_id['channel_id'])
    assert details['all_members'] == [
            {'u_id': 0, 'name_first': 'First', 'name_last': 'Last', 'profile_img_url': 'default.jpg'}, 
            {'u_id': 1, 'name_first': 'First2', 'name_last': 'Last2', 'profile_img_url': 'default.jpg'}
    ]
