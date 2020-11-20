'''
channel_details_http_test.py

Fixtures:
    register_and_login_user: registers a user and logs that user in

Test Modules:
    test_details_valid: tests when token and channel_id is valid
    test_invalid_channel_id_negative: tests when channel_id is negative
    test_invalid_channel_id_char: tests when channel_id is contains a character                                                       
    test_unauthorised_member: tests when user token not authorised                                                                                                                                                         
    test_test_invalid_owner_add: tests when authorised user is not an owner, but is trying to make someone else an owner.                                                                                                                                                                          
    test_details_valid_after_invite: tests success case where token and channel_id is valid.
'''
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import pytest
from implement.channel        import channel_details, channel_invite
from implement.channels       import channels_create
from error          import InputError, AccessError
from implement.other          import clear
from implement.auth import auth_register, auth_login

@pytest.fixture
def register_and_login_user():
    clear()
    auth_register("test@email.com", "password", "Angus", "Doe")
    login = auth_login("test@email.com", "password")
    token = login['token']
    return token

def test_details_valid(register_and_login_user):
    token = register_and_login_user

    # Create another user and a channel before it to not retrieve it
    auth_register("test2@email.com", "password", "Angus", "Doe")
    login = auth_login("test2@email.com", "password")
    channels_create(login['token'], "ignore channel", True)

    channels_create(token, "test channel", True)
    result = channel_details(token, 1)

    assert result == {
        'name': 'test channel',
        'owner_members': [
            {
                'u_id': 0,
                'name_first': 'Angus',
                'name_last': 'Doe',
                'profile_img_url': 'default.jpg',
            }
        ],
        'all_members': [
            {
                'u_id': 0,
                'name_first': 'Angus',
                'name_last': 'Doe',
                'profile_img_url': 'default.jpg',
            }
        ]
    }

# test should raise InputError since no channel with negative ID 
def test_invalid_channel_id_negative(register_and_login_user):
    token = register_and_login_user
    channels_create(token, "test channel", True)
    with pytest.raises(InputError):
        channel_details(token, -42)

# test should raise InputError since no channel contains letters in ID 
def test_invalid_channel_id_char(register_and_login_user):
    register_and_login_user
    token = register_and_login_user
    channels_create(token, "test channel", True)
    with pytest.raises(InputError):
        channel_details(token, 'a')


# test should raise AccessError since other@email.com user is not a member
def test_unauthorised_member(register_and_login_user):
    token = register_and_login_user
    channels_create(token, "test channel", True)

    auth_register("other@email.com", "password", "Abus", "Doe")
    user = auth_login("other@email.com", "password")
    token = user['token']

    with pytest.raises(AccessError):
        channel_details(token, 0)

def test_details_valid_after_invite(register_and_login_user):
    token = register_and_login_user
    channels_create(token, "test channel", True)

    auth_register("other@email.com", "password", "Lmao", "Bus")
    login = auth_login("other@email.com", "password")
    token = login['token']

    channel_invite(token, 0, 1)

    result = channel_details(token, 0)
    assert result == {
        'name': 'test channel',
        'owner_members': [
            {
                'u_id': 0,
                'name_first': 'Angus',
                'name_last': 'Doe',
                'profile_img_url': 'default.jpg',
            }
        ],
        'all_members': [
            {
                'u_id': 0,
                'name_first': 'Angus',
                'name_last': 'Doe',
                'profile_img_url': 'default.jpg',
            },
            {
                'u_id': 1,
                'name_first': 'Lmao',
                'name_last': 'Bus',
                'profile_img_url': 'default.jpg',
            },
        ]
    }
