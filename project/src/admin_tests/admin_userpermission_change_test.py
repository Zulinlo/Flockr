"""
admin_userpermission_change_test.py

Helper Modules:
    is_flockr_owner: takes in a u_id and returns True if u_id is a flockr owner and else False

Fixtures:
    flockr_owner: creates a flockr owner
    register_user: creates a user who is not a flockr owner

Test Modules:
    test_invalid_token: tests for invalid token
    test_invalid_u_id: expects InputError when u_id does not exist
    test_invalid_permission_id: expects InputError when permission_id is not valid
    test_invalid_flockr_owner: authorised user is not a Flockr owner expecting AccessError
    test_valid_flockr_owner_target_themselves: to make sure an owner can change any owner's permissions by changing their own permissions
    test_valid_flockr_owner_changing_to_same_permission: to make sure an owner can change a member's permissions to the same permission
    test_valid_flockr_owner_making_flockr_owner: to make sure a Flockr owner can make Flockr owners
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import pytest
from error                  import InputError, AccessError
from implement.other                  import clear, admin_userpermission_change
from implement.auth         import auth_register, auth_login
from helper                 import is_flockr_owner, token_hash

@pytest.fixture
def flockr_owner():
    clear()
    auth_register("flockrowner@gmail.com", "password", "God", "Doe")
    flockr_owner = auth_login("flockrowner@gmail.com", "password")

    return flockr_owner

@pytest.fixture
def register_user():
    auth_register("user@gmail.com", "password", "user", "Doe")
    user = auth_login("user@gmail.com", "password")
     
    return user

def test_invalid_token():
    with pytest.raises(AccessError):
        admin_userpermission_change(token_hash(-1), 0, 2)

def test_invalid_u_id(flockr_owner):
    owner = flockr_owner

    # Expect InputError when user does not exist
    with pytest.raises(InputError):
        admin_userpermission_change(owner['token'], 'not_valid_u_id', 1)

def test_invalid_permission_id(flockr_owner, register_user):
    owner = flockr_owner
    register_user

    # Expect InputError when permission_id is not 1 or 2
    with pytest.raises(InputError):
        admin_userpermission_change(owner['token'], 1, 3)

def test_invalid_flockr_owner(flockr_owner, register_user):
    flockr_owner
    user = register_user

    # Expect AccessError when authorised user is not an owner
    with pytest.raises(AccessError):
        admin_userpermission_change(user['token'], user['u_id'], 1)

def test_valid_flockr_owner_target_themselves(flockr_owner):
    owner = flockr_owner

    admin_userpermission_change(owner['token'], owner['u_id'], 2)

    # Make sure the owner is now a member
    assert not is_flockr_owner(owner['token'], owner['u_id'])
    
def test_valid_flockr_owner_changing_to_same_permission(flockr_owner):
    owner = flockr_owner

    admin_userpermission_change(owner['token'], owner['u_id'], 1)

    # Make sure the owner is still an owner with no errors raised
    assert is_flockr_owner(owner['token'], owner['u_id'])

def test_valid_flockr_owner_making_flockr_owner(flockr_owner, register_user):
    owner = flockr_owner
    user = register_user

    admin_userpermission_change(owner['token'], user['u_id'], 1)

    # Make sure the user is now a Flockr owner
    assert is_flockr_owner(user['token'], user['u_id'])
