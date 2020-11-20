'''
channel_invite_http_test.py

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
import re
from subprocess import Popen, PIPE
import signal
from time       import sleep
import requests
import json
import urllib

from error      import InputError, AccessError
from helper     import token_hash

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
        "name_first": "First",
        "name_last": "Last"
    })
    
    r = requests.post(f"{url}/auth/login", json={
        'email': 'test@email.com', 
        'password': 'password'
    })
    payload = r.json()

    return payload

# AccessError: token passed in is invalid
def test_invalid_token(url, register_and_login_user):
    user = register_and_login_user

    r = requests.post(f"{url}/channels/create", json={
        'token': user['token'],
        'name': 'Channel',
        'is_public': False
    })
    c_id = r.json()

    invalid_token = token_hash(1)

    r = requests.post(f"{url}/channel/invite", json={
        'token': invalid_token,
        'channel_id': c_id['channel_id'],
        'u_id': user['u_id']
    })
    payload = r.json()
    assert payload['code'] == 400

# InputError: channel_id does not refer to a valid channel.
def test_invalid_channel_id(url, register_and_login_user):
    user = register_and_login_user
    
    invalid_c_id = -1
    r = requests.post(f"{url}/channel/invite", json={
        'token': user['token'],
        'channel_id': invalid_c_id,
        'u_id': user['u_id']
    })
    payload = r.json()
    assert payload['code'] == 400

# InputError: u_id does not refer to a valid user
def test_invalid_u_id(url, register_and_login_user):
    user = register_and_login_user

    r = requests.post(f"{url}/channels/create", json={
        'token': user['token'],
        'name': 'Channel',
        'is_public': False
    })
    c_id = r.json()

    invalid_u_id = -1
    r = requests.post(f"{url}/channel/invite", json={
        'token': user['token'],
        'channel_id': c_id['channel_id'],
        'u_id': invalid_u_id
    })
    payload = r.json()
    assert payload['code'] == 400

# Check that the user can't invite themselves
def test_invalid_reinvite(url, register_and_login_user):
    user = register_and_login_user

    r = requests.post(f"{url}/channels/create", json={
        'token': user['token'],
        'name': 'Channel',
        'is_public': False
    })
    c_id = r.json()

    r = requests.post(f"{url}/channel/invite", json={
        'token': user['token'],
        'channel_id': c_id['channel_id'],
        'u_id': user['u_id']
    })
    payload = r.json()
    assert payload['code'] == 400

# Check that a user who is in the channel can invite another
# user who is not in the channel
def test_invite_success(url, register_and_login_user):
    user_1 = register_and_login_user
    
    requests.post(f"{url}/auth/register", json={
        "email": "test2@email.com",
        "password": "password2",
        "name_first": "First2",
        "name_last": "Last2"
        })
    
    r = requests.post(f"{url}/auth/login", json={
        'email': 'test2@email.com', 
        'password': 'password2'
    })
    user_2 = r.json()

    r = requests.post(f"{url}/channels/create", json={
        'token': user_1['token'],
        'name': 'User_1s Channel',
        'is_public': False
    })
    c_id = r.json()

    requests.post(f"{url}/channel/invite", json={
        'token': user_1['token'],
        'channel_id': c_id['channel_id'],
        'u_id': user_2['u_id']
    })

    queryString = urllib.parse.urlencode({
        'token': user_1['token'],
        'channel_id': c_id['channel_id']
    })
    r = requests.get(f"{url}/channel/details?{queryString}")
    details = r.json()
    for members in details['all_members']:
        members['profile_img_url'] = 'default.jpg'

    assert details['all_members'] == [
            {'u_id': 0, 'name_first': 'First', 'name_last': 'Last', 'profile_img_url': 'default.jpg'}, 
            {'u_id': 1, 'name_first': 'First2', 'name_last': 'Last2', 'profile_img_url': 'default.jpg'}
    ]
