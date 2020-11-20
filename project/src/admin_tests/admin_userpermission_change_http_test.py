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
import re
import signal
import json
import requests
import urllib

from helper                 import token_hash, is_flockr_owner
from subprocess             import Popen, PIPE
from time                   import sleep

@pytest.fixture
def url():
    url_re = re.compile(r' \* Running on ([^ ]*)')
    server = Popen(["python3", "src/server.py"], stderr=PIPE, stdout=PIPE)
    line = server.stderr.readline()
    local_url = url_re.match(line.decode())
    if local_url:
        yield local_url.group(1)
        # Terminate the server
        server.send_signal(signal.SIGINT)
        waited = 0
        while server.poll() is None and waited < 5:
            sleep(0.1)
            waited += 0.1
        if server.poll() is None:
            server.kill()
    else:
        server.kill()
        raise Exception("Couldn't get URL from local server")

@pytest.fixture
def flockr_owner(url):
    requests.delete(f"{url}/clear")
    requests.post(f"{url}/auth/register", json={
        "email":"flockrowner@gmail.com", 
        "password": "password", 
        "name_first": "God", 
        "name_last": "Doe"
    })
    result = requests.post(f"{url}/auth/login", json={
        "email":"flockrowner@gmail.com", 
        "password": "password"
    })
    payload = result.json()
    return payload

@pytest.fixture
def register_login(url):
    # Fixture registers a user and then logs them in
    # Returns dictionary containing their u_id and token.
    # Create dummy user to make sure right user is being targetted
    requests.post(f"{url}/auth/register", json={
        "email":"user@gmail.com", 
        "password": "password", 
        "name_first": "Angus", 
        "name_last": "Doe"
    })
    result = requests.post(f"{url}/auth/login", json={
        "email":"user@gmail.com", 
        "password": "password"
    })
    payload = result.json()
    return payload

def test_invalid_token(url):
    invalid_token = token_hash(-1)
    result = requests.post(f"{url}/admin/userpermission/change", json={
        "token": invalid_token, 
        "u_id": 0, 
        "permission_id": 2
    })
    payload = result.json()
    assert payload['code'] == 400

def test_invalid_u_id(url, flockr_owner):
    owner = flockr_owner
    
    # Expect InputError when user does not exist
    result = requests.post(f"{url}/admin/userpermission/change", json={
        "token": owner['token'], 
        "u_id": 'not_valid_u_id', 
        "permission_id": 1
    })
    payload = result.json()
    assert payload['code'] == 400

def test_invalid_permission_id(url, flockr_owner):
    owner = flockr_owner

    # Expect InputError when permission_id is not 1 or 2
    result = requests.post(f"{url}/admin/userpermission/change", json={
        "token": owner['token'], 
        "u_id": 1, 
        "permission_id": 3
    })
    payload = result.json()
    assert payload['code'] == 400

def test_invalid_flockr_owner(url, flockr_owner, register_login):
    user = register_login

    # Expect AccessError when authorised user is not an owner
    result = requests.post(f"{url}/admin/userpermission/change", json={
        "token": user['token'], 
        "u_id": user['u_id'], 
        "permission_id": 1
    })
    payload = result.json()
    assert payload['code'] == 400

def test_valid_flockr_owner_target_themselves(url, flockr_owner):
    owner = flockr_owner

    requests.post(f"{url}/admin/userpermission/change", json={
        "token": owner['token'], 
        "u_id": owner['u_id'], 
        "permission_id": 2
    })
    queryString = urllib.parse.urlencode({
        'token': owner['token'],
        'u_id': owner['u_id']
    })
    # Make sure the owner is now a member
    result = requests.get(f"{url}/user/profile?{queryString}")
    payload = result.json()['user'] 
    assert payload['permission_id'] == 2

def test_valid_flockr_owner_changing_to_same_permission(url, flockr_owner):
    owner = flockr_owner

    requests.post(f"{url}/admin/userpermission/change", json={
        "token": owner['token'], 
        "u_id": owner['u_id'], 
        "permission_id": 1
    })

    queryString = urllib.parse.urlencode({
        'token': owner['token'],
        'u_id': owner['u_id']
    })

    # Make sure the owner is still an owner with no errors raised
    result = requests.get(f"{url}/user/profile?{queryString}")
    payload = result.json()['user'] 
    assert payload['permission_id'] == 1

def test_valid_flockr_owner_making_flockr_owner(url, flockr_owner, register_login):
    owner = flockr_owner
    user = register_login

    requests.post(f"{url}/admin/userpermission/change", json={
        "token": owner['token'], 
        "u_id": user['u_id'], 
        "permission_id": 1
    })
    
    queryString = urllib.parse.urlencode({
        'token': owner['token'],
        'u_id': owner['u_id']
    })
    
    # Make sure the user is now a Flockr owner
    result = requests.get(f"{url}/user/profile?{queryString}")
    payload = result.json()['user'] 
    assert payload['permission_id'] == 1
