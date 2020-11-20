"""
users_all_test.py

Test Modules:
    test_success_one_user: success case for when there's one user
    test_success_multiple_users: success case for when there's multiple users
    test_fail: fail case due to invalid token
   
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import pytest
from implement.other          import users_all
from implement.auth import auth_register, auth_login
from error          import AccessError
from implement.other        import clear
from helper         import token_hash, password_hash

# Success Cases
# Success case when only one user is made
def test_success_one_user():
    clear()
    auth_register("test@gmail.com", "pass123", "Wilson", "Doe")
    user = auth_login("test@gmail.com", "pass123")
    display_users = users_all(user['token'])
    assert display_users == {'users': [
        {
            'u_id': 0, 
            'email': 'test@gmail.com',
            'name_first': 'Wilson',
            'name_last': 'Doe',
            'handle_str': 'wilsondoe',
            'profile_img_url': 'default.jpg'
        }
    ]}

# Success case for when there are multiple users
def test_success_multiple_users():
    clear()
    auth_register("test@gmail.com", "pass123", "Wilson", "Doe")
    user = auth_login("test@gmail.com", "pass123")
    auth_register("test2@gmail.com", "pass123", "Bilson", "Doe")
    auth_login("test2@gmail.com", "pass123")
    display_users = users_all(user['token'])
    assert display_users == {'users': [
        {
            'u_id': 0,
            'email': 'test@gmail.com',
            'name_first': 'Wilson',
            'name_last': 'Doe',
            'handle_str': 'wilsondoe',
            'profile_img_url': 'default.jpg'
        },
        {
            'u_id': 1,
            'email': 'test2@gmail.com',
            'name_first': 'Bilson',
            'name_last': 'Doe',
            'handle_str': 'bilsondoe',
            'profile_img_url': 'default.jpg'
        }
    ]}

# Fail Cases

# Fail Case due to invalid token
def test_fail():
    clear()
    auth_register("test@gmail.com", "password", "Wilson", "Doe")
    auth_login("test@gmail.com", "password")
    with pytest.raises(AccessError):
        users_all(token_hash(1))
    
