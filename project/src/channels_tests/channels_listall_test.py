'''
channel_listall_test.py

Fixtures:
    register_and_login_user: registers a user and logs that user in

Test Modules:
    test_valid_token: tests when token matches corresponding user's token
    test_list_multiple: tests when multiple channels need to be listed
    test_invalid_token: tests when token doesn't matche corresponding user's token                                                                                                                                                                               
'''
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import pytest
from implement.other          import clear
from error          import InputError, AccessError
from implement.auth           import auth_register, auth_login
from implement.channels       import channels_create, channels_listall
from helper         import token_hash

@pytest.fixture
def register_and_login_user():
    clear()
    auth_register("test@email.com", "password", "Angus", "Doe")
    login = auth_login("test@email.com", "password")
    token = login['token']
    return token

# should return list of all channels since token is valid
def test_valid_token(register_and_login_user):   
    token = register_and_login_user
    channels_create(token, "test channel", True)
    result = channels_listall(token)
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
        ]
    }

def test_list_multiple(register_and_login_user):
    token = register_and_login_user
    channels_create(token, "test1 channel", True)
    channels_create(token, "test2 channel", True)
    channels_create(token, "test3 channel", True)
    result = channels_listall(token)
    assert result == {'channels': [
            {
                'channel_id': 0,
                'name': 'test1 channel',
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
            },
            {
                'channel_id': 2,
                'name': 'test3 channel',
                'owner_members': [0],
                'all_members': [0],
                'is_public': True,
                'time_finish': None,
                'messages': [],
            }
        ]
    }

# should throw error since token will be invalid
def test_invalid_token(register_and_login_user):
    token = register_and_login_user
    channels_create(token, "test channel", True)
    with pytest.raises(AccessError):
        channels_listall(token_hash(1))
