'''
channel_leave_http_test.py

Fixtures:
    register_new_user: registers a user and logs that user in

Test Modules:
    test_channel_leave: tests success case where token and channel_id are valid
    test_user_already_in_channel: tests when user trying to join is already in channel
    test_test_invalid_channel_id: tests when channel_id is a negative number                                                  
    test_private_channel: tests when channel is private and user is not an owner                                                                                                                                                     
    test_second_user_added: tests to see if second user can be added after first user is added.
'''
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import re
import signal
import requests
import json
import pytest
from subprocess     import Popen, PIPE
from time           import sleep
from error          import InputError, AccessError
from helper         import token_hash
import urllib

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
def register_new_user(url):
    requests.delete(f"{url}/clear")
    requests.post(f"{url}/auth/register", json={
        "email":"test@gmail.com", 
        "password": "password", 
        "name_first": "Wilson", 
        "name_last": "Doe"
    })
    r = requests.post(f"{url}/auth/login", json={
        'email': 'test@gmail.com', 
        'password': 'password'
    })
    payload = r.json()
    return payload

# Success Case
def test_channel_leave(url, register_new_user):
    
    new_user = register_new_user    
    token = new_user['token']

    r = requests.post(f"{url}/channels/create", json={
        'token': token,
        'name': 'Test Channel',
        'is_public': True
    })
    
    channel = r.json()
    c_id = channel['channel_id']
    in_channel = True

    requests.post(f"{url}/auth/register", json={
        "email":"test@gmail2.com",
        "password": "password1",
        "name_first": "Bilson",
        "name_last": "Doe"
    })
    r = requests.post(f"{url}/auth/login", json={
        'email': 'test@gmail2.com',
        'password': 'password1'
    })
    user2 = r.json()

    requests.post(f"{url}/channel/join", json={
        'token': user2['token'],
        'channel_id': c_id,
    })

    # Check if member is no longer in channel
    requests.post(f"{url}/channel/leave", json={
        'token': new_user['token'],
        'channel_id': c_id,
    })

    queryString = urllib.parse.urlencode({
        'token': user2['token'],
        'channel_id': c_id
    })
    result = requests.get(f"{url}/channel/details?{queryString}")
    member_check = result.json()
    in_channel = new_user['u_id'] in member_check['all_members']
    
    assert in_channel == False

# Assumption: Channels increment from 0 onwards. Therefore any negative values for c_id are invalid
def test_channel_leave_invalid_channel(url, register_new_user):
    new_user = register_new_user

    requests.post(f"{url}/channels/create", json={
        'token': new_user['token'],
        'name': 'Test Channel',
        'is_public': True
    })
    r = requests.post(f"{url}/channel/leave", json={
        'token': new_user['token'],
        'channel_id': -10,
    })
    payload = r.json()
    assert payload['code'] == 400

#User cannot leave channel when they haven't joined it
def test_channel_leave_unauthorised(url, register_new_user):
    new_user = register_new_user

    r = requests.post(f"{url}/channels/create", json={
        'token': new_user['token'],
        'name': 'Test Channel',
        'is_public': True
    })
    channel = r.json()

    requests.post(f"{url}/auth/register", json={
        "email":"test@gmail2.com",
        "password": "password1",
        "name_first": "Bilson",
        "name_last": "Doe"
    })
    u = requests.post(f"{url}/auth/login", json={
        'email': 'test@gmail2.com',
        'password': 'password1'
    })
    user2 = u.json()
    unjoined_token = user2['token']

    r = requests.post(f"{url}/channel/leave", json={
        'token': unjoined_token,
        'channel_id': channel['channel_id'],
    })
    payload = r.json()
    assert payload['code'] == 400

# Access Error due to invalid token
def test_invalid_token(url, register_new_user):
    new_user = register_new_user

    c = requests.post(f"{url}/channels/create", json={
        'token': new_user['token'],
        'name': 'Test Channel',
        'is_public': True
    })
    channel = c.json()
    c_id = channel['channel_id']

    invalid_token = token_hash(1)
    r = requests.post(f"{url}/channel/leave", json={
        'token': invalid_token,
        'channel_id': c_id
    })
    payload = r.json()
    assert payload['code'] == 400
