'''
channel_join_http_test.py

Fixtures:
    register_user: registers a user and logs that user in

Test Modules:
    test_invalid_token: tests when token is invalid
    test_user_already_in_channel: tests when user trying to join is already in channel
    test_test_invalid_channel_id: tests when channel_id is a negative number                                                  
    test_private_channel: tests when channel is private and user is not an owner                                                                                                                                                     
    test_second_user_added: tests to see if second user can be added after first user is added.
'''
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import re
from subprocess     import Popen, PIPE
import signal
from time           import sleep
import requests
import json
import pytest
import urllib

from error          import InputError, AccessError
from helper         import token_hash

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
def register_login_user(url):
    requests.delete(f"{url}/clear")
    requests.post(f"{url}/auth/register", json={
        "email":"user@email.com", 
        "password": "password", 
        "name_first": "First", 
        "name_last": "Last"
    })
    r = requests.post(f"{url}/auth/login", json={
        'email': 'user@email.com', 
        'password': 'password'
    })
    payload = r.json()
    return payload['token']

# Success Cases
def test_second_user_added(url, register_login_user):
    token_1 = register_login_user

    # Register and login second user
    requests.post(f"{url}/auth/register", json={
        "email":"user2@email.com", 
        "password": "password", 
        "name_first": "First", 
        "name_last": "Last"
    })
    r = requests.post(f"{url}/auth/login", json={
        'email': 'user2@email.com', 
        'password': 'password'
    })
    user = r.json()
    token_2 = user['token']

    # Create channel with first user
    c = requests.post(f"{url}/channels/create", json={
        'token': token_1,
        'name': 'Channel',
        'is_public': True
    })
    channel = c.json()
    c_id = channel['channel_id']
    
    # Second member joins channel
    requests.post(f"{url}/channel/join", json={
        'token': token_2,
        'channel_id': c_id,
    })

    queryString = urllib.parse.urlencode({
        'token': token_1,
        'channel_id': c_id
    })
    # Retrieve channel details
    result = requests.get(f"{url}/channel/details?{queryString}")

    payload = result.json()
    for members in payload['all_members']:
        members['profile_img_url'] = 'default.jpg'
    assert payload['all_members'] == [
            {'u_id': 0, 'name_first': 'First', 'name_last': 'Last', 'profile_img_url': 'default.jpg'},
            {'u_id': 1, 'name_first': 'First', 'name_last': 'Last', 'profile_img_url': 'default.jpg'}
    ]

def test_flockr_owner(url, register_login_user):
    flockr_owner = register_login_user

    # Register and login second user
    requests.post(f"{url}/auth/register", json={
        "email":"owner@email.com", 
        "password": "password", 
        "name_first": "First", 
        "name_last": "Last"
    })
    r = requests.post(f"{url}/auth/login", json={
        'email': 'owner@email.com', 
        'password': 'password'
    })
    user = r.json()
    owner = user['token']

    # Create channel with second user
    c = channel = requests.post(f"{url}/channels/create", json={
        'token': owner,
        'name': 'Channel',
        'is_public': False
    })
    channel = c.json()
    c_id = channel['channel_id']

    # Flockr Owner joins channel
    requests.post(f"{url}/channel/join", json={
        'token': flockr_owner,
        'channel_id': c_id,
    })

    queryString = urllib.parse.urlencode({
        'token': owner,
        'channel_id': c_id
    })
    # Retrieve channel details
    result = requests.get(f"{url}/channel/details?{queryString}")

    payload = result.json()
    for member in payload['all_members']:
        member['profile_img_url'] = 'default.jpg'
    assert payload['all_members'] == [
            {'u_id': 1, 'name_first': 'First', 'name_last': 'Last', 'profile_img_url': 'default.jpg'},
            {'u_id': 0, 'name_first': 'First', 'name_last': 'Last', 'profile_img_url': 'default.jpg'}
    ]

'''Fail Cases'''
def test_invalid_token(url, register_login_user):
    token = register_login_user
    channel = requests.post(f"{url}/channels/create", json={
        'token': token,
        'name': 'Channel',
        'is_public': True
    })
    c_id = channel.json()['channel_id']

    token = token_hash(1)
    r = requests.post(f"{url}/channel/join", json={
        'token': token,
        'channel_id': c_id
    })
    payload = r.json()
    assert payload['code'] == 400


def test_user_already_in_channel(url, register_login_user):
    token = register_login_user
    channel = requests.post(f"{url}/channels/create", json={
        'token': token,
        'name': 'Channel',
        'is_public': True
    })
    c_id = channel.json()['channel_id']
    r = requests.post(f"{url}/channel/join", json={
        'token': token,
        'channel_id': c_id
    })
    payload = r.json()
    assert payload['code'] == 400

def test_invalid_channel_id(url, register_login_user):
    token = register_login_user
    r = requests.post(f"{url}/channel/join", json={
        'token': token,
        'channel_id': -1
    })
    payload = r.json()
    assert payload['code'] == 400

def test_private_channel(url, register_login_user):
    owner = register_login_user

    # Register and login second user
    requests.post(f"{url}/auth/register", json={
        "email":"user2@email.com", 
        "password": "password", 
        "name_first": "First", 
        "name_last": "Last"
    })
    t = requests.post(f"{url}/auth/login", json={
        'email': 'user2@email.com', 
        'password': 'password'
    })
    user = t.json()
    token_2 = user['token']

    # Create channel with first user
    c = requests.post(f"{url}/channels/create", json={
        'token': owner,
        'name': 'Channel',
        'is_public': False
    })
    channel = c.json()
    c_id = channel['channel_id']

    # Attempt to join with second user
    r = requests.post(f"{url}/channel/join", json={
        'token': token_2,
        'channel_id': c_id
    })
    payload = r.json()
    assert payload['code'] == 400
