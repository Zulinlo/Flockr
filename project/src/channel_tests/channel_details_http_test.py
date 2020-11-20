'''
channel_details_http_test.py

Fixtures:
    register_and_login_user: registers a user and logs that user in

Test Modules:
    test_details_valid: tests when token and channel_id is valid
    test_invalid_channel_id_negative: tests when channel_id is negative
    test_invalid_channel_id_char: tests when channel_id is contains a character                                                       test_unauthorised_member: tests when user token not authorised                                                                                                                                                         
    test_test_invalid_owner_add: tests when authorised user is not an owner, but is trying to make someone else an owner.                                                                                                                                                                          
    test_details_valid_after_invite: tests success case where token and channel_id is valid.
'''
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import pytest
import re
import signal
import json
import requests
import urllib

from error      import InputError, AccessError
from subprocess import Popen, PIPE
from time       import sleep


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
def register_and_login_user(url):
    requests.delete(f"{url}/clear")
    requests.post(f"{url}/auth/register", json={
        "email": "test@email.com", 
        "password": "password", 
        "name_first":  "Angus", 
        "name_last": "Doe"
    })
    login = requests.post(f"{url}/auth/login", json={
        "email": "test@email.com",
        "password": "password"
    })
    payload = login.json()
    return payload['token']

def test_details_valid(url, register_and_login_user):
    token = register_and_login_user

    # auth_register("test2@email.com", "password", "Angus", "Doe")
    requests.post(f"{url}/auth/register", json={
        "email": "test2@email.com", 
        "password": "password", 
        "name_first": "Angus", 
        "name_last": "Doe"
    })
    r = requests.post(f"{url}/auth/login", json={
        "email": "test2@email.com", 
        "password": "password"
    })
    token_2 = r.json()['token']

    requests.post(f"{url}/channels/create", json={
        "token": token_2, 
        "name": "ignore channel", 
        "is_public": True
    })

    requests.post(f"{url}/channels/create", json={
        "token": token, 
        "name": "test channel", 
        "is_public": True
    })

    queryString = urllib.parse.urlencode({
        "token": token, 
        "channel_id": 1
    })
    r = requests.get(f"{url}/channel/details?{queryString}")
    payload = r.json() 

    # Because unable to get image url because request.host cannot be ran and so unable to retrieve dns
    for owner in payload['owner_members']:
        owner['profile_img_url'] = 'default.jpg'
    
    for member in payload['all_members']:
        member['profile_img_url'] = 'default.jpg'

    assert payload == {
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
def test_invalid_channel_id_negative(url, register_and_login_user):
    token = register_and_login_user
    requests.post(f"{url}/channels/create", json={
        "token": token, 
        "name": "test channel", 
        "is_public": True
    })

    queryString = urllib.parse.urlencode({
        "token": token, 
        "channel_id": -42
    })
    result = requests.get(f"{url}/channel/details?{queryString}")
    payload = result.json()

    assert payload['code'] == 400

# test should raise InputError since no channel contains letters in ID 
def test_invalid_channel_id_char(url, register_and_login_user):
    register_and_login_user
    token = register_and_login_user
    requests.post(f"{url}/channels/create", json={
        "token": token, 
        "name": "test channel", 
        "is_public": True
    })

    queryString = urllib.parse.urlencode({
        "token": token, 
        "channel_id": -1
    })
    result = requests.get(f"{url}/channel/details?{queryString}")
    payload = result.json()

    assert payload['code'] == 400

# test should raise AccessError since other@email.com user is not a member
def test_unauthorised_member(url, register_and_login_user):
    token = register_and_login_user
    requests.post(f"{url}/channels/create", json={
        "token": token, 
        "name": "test channel", 
        "is_public": True
    })

    requests.post(f"{url}/auth/register", json={
        "email": "other@email.com", 
        "password": "password", 
        "name_first": "Abus", 
        "name_last": "Doe"
    })
    user = requests.post(f"{url}/auth/login", json={
        "email": "other@email.com", 
        "password": "password"
    })
    payload = user.json()

    queryString = urllib.parse.urlencode({
        "token": payload['token'], 
        "channel_id": 0
    })
    r = requests.get(f"{url}/channel/details?{queryString}")
    result = r.json()

    assert result['code'] == 400

def test_details_valid_after_invite(url, register_and_login_user):
    token = register_and_login_user
    requests.post(f"{url}/channels/create", json={
        "token": token, 
        "name": "test channel", 
        "is_public": True
    })

    requests.post(f"{url}/auth/register", json={
        "email": "other@email.com", 
        "password": "password", 
        "name_first": "Lmao", 
        "name_last": "Bus"
    })
    user = requests.post(f"{url}/auth/login", json={
        "email": "other@email.com", 
        "password": "password"
    })
    payload = user.json()
    
    requests.post(f"{url}/channel/invite", json={
        "token": payload['token'], 
        "channel_id": 0, 
        "u_id": 1
    })

    queryString = urllib.parse.urlencode({
        "token": payload['token'], 
        "channel_id": 0
    })
    result = requests.get(f"{url}/channel/details?{queryString}")
    payload = result.json()

    # Because unable to get image url because request.host cannot be ran and so unable to retrieve dns
    for owner in payload['owner_members']:
        owner['profile_img_url'] = 'default.jpg'
    
    for member in payload['all_members']:
        member['profile_img_url'] = 'default.jpg'

    assert payload == {
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
