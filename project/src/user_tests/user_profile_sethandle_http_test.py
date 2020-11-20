'''
user_profile_sethandle_http_test.py

Fixtures:
    register_login: registers a user and logs that user in

Test Modules:
    test_valid_handle_str: tests valid handle where no errors should be raised
    test_same_handle: tests when new handle is already in use
    test_invalid_short3: tests when new handle is exactly 3 characters long 
    test_invalid_short: tests when new handle is less than 3 characters long
    test_invalid_long20: tests when new handle is exaclty 20 characters long
    test_invalid_long: tests when new handle is more than 20 characters long
'''
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import pytest
import re
import signal
import json
import requests
import urllib

from helper         import token_hash
from subprocess     import Popen, PIPE
from time           import sleep

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
def register_login(url):
    requests.delete(f"{url}/clear")
    # Fixture registers a user and then logs them in
    # Returns dictionary containing their u_id and token.
    # Create dummy user to make sure right user is being targetted
    requests.post(f"{url}/auth/register", json={
        "email":"ignore@email.com", 
        "password": "password", 
        "name_first": "Bungus", 
        "name_last": "Boe"
    })
    requests.post(f"{url}/auth/register", json={
        "email":"test@gmail.com", 
        "password": "password", 
        "name_first": "Angus", 
        "name_last": "Doe"
    })
    result = requests.post(f"{url}/auth/login", json={
        "email":"test@gmail.com", 
        "password": "password"
    })
    payload = result.json()
    return payload

def test_valid_handle_str(url, register_login):
    # Setting up valid token to be passed into user_profile_sethandle.
    user = register_login
    token = user["token"]
    u_id = user["u_id"]

    queryString = urllib.parse.urlencode({
        "token": token, 
        "u_id": u_id
    })
    result = requests.get(f"{url}/user/profile?{queryString}")
    profile = result.json()['user']
    
    # Current handle should be default concatenation of first and last name.
    current_handle = profile['handle_str']
    assert current_handle == 'angusdoe'
    
    # handle_str will be valid since unique and between 3 & 20 characters.
    handle_str = 'test_new_handle'
    requests.put(f"{url}/user/profile/sethandle", json={
        "token": token, 
        "handle_str": handle_str
    })

    queryString = urllib.parse.urlencode({
        "token": token, 
        "u_id": u_id
    })
    # Since all inputs are valid, the users handle should be updated as 
    # 'test_new_handle'
    result = requests.get(f"{url}/user/profile?{queryString}")
    new_handle = result.json()['user']['handle_str']
    assert new_handle == handle_str

def test_same_handle(url, register_login):
    # Setting up valid token to be passed into user_profile_sethandle.
    user = register_login
    token = user["token"]
    u_id = user["u_id"]

    queryString = urllib.parse.urlencode({
        "token": token, 
        "u_id": u_id
    })
    result = requests.get(f"{url}/user/profile?{queryString}")
    profile = result.json()['user']

    # Current handle should be default concatenation of first and last name.
    current_handle = profile['handle_str']
    assert current_handle == 'angusdoe'

    # handle_str will be invalid as current user already using that handle 
    handle_str = 'angusdoe'
    result = requests.put(f"{url}/user/profile/sethandle", json={
        "token": token, 
        "handle_str": handle_str
    })
    payload = result.json()
    assert payload['code'] == 400

def test_invalid_short3(url, register_login):
    # Setting up valid token to be passed into user_profile_sethandle.
    user = register_login
    token = user["token"]
    u_id = user["u_id"]

    queryString = urllib.parse.urlencode({
        "token": token, 
        "u_id": u_id
    })
    result = requests.get(f"{url}/user/profile?{queryString}")
    profile = result.json()['user']

    # Current handle should be default concatenation of first and last name.
    current_handle = profile['handle_str']
    assert current_handle == 'angusdoe'

    # handle_str will be invalid as it is 3 characters
    handle_str = 'xdd'
    result = requests.put(f"{url}/user/profile/sethandle", json={
        "token": token, 
        "handle_str": handle_str
    })
    payload = result.json()
    assert payload['code'] == 400

def test_invalid_short(url, register_login):
    # Setting up valid token to be passed into user_profile_sethandle.
    user = register_login
    token = user["token"]
    u_id = user["u_id"]

    queryString = urllib.parse.urlencode({
        "token": token, 
        "u_id": u_id
    })
    result = requests.get(f"{url}/user/profile?{queryString}")
    profile = result.json()['user']

    # Current handle should be default concatenation of first and last name.
    current_handle = profile['handle_str']
    assert current_handle == 'angusdoe'

    # handle_str will be invalid as it is less than 3 characters
    handle_str = 'xdd'
    result = requests.put(f"{url}/user/profile/sethandle", json={
        "token": token, 
        "handle_str": handle_str
    })
    payload = result.json()
    assert payload['code'] == 400

def test_invalid_long20(url, register_login):
    # Setting up valid token to be passed into user_profile_sethandle.
    user = register_login
    token = user["token"]
    u_id = user["u_id"]

    queryString = urllib.parse.urlencode({
        "token": token, 
        "u_id": u_id
    })
    result = requests.get(f"{url}/user/profile?{queryString}")
    profile = result.json()['user']

    # Current handle should be default concatenation of first and last name.
    current_handle = profile['handle_str']
    assert current_handle == 'angusdoe'

    # handle_str will be invalid as it is 20 characters
    handle_str = '01234567890123456789'
    result = requests.put(f"{url}/user/profile/sethandle", json={
        "token": token, 
        "handle_str": handle_str
    })
    payload = result.json()
    assert payload['code'] == 400

def test_invalid_long(url, register_login):
    # Setting up valid token to be passed into user_profile_sethandle.
    user = register_login
    token = user["token"]
    u_id = user["u_id"]

    queryString = urllib.parse.urlencode({
        "token": token, 
        "u_id": u_id
    })
    result = requests.get(f"{url}/user/profile?{queryString}")
    profile = result.json()['user']

    # Current handle should be default concatenation of first and last name.
    current_handle = profile['handle_str']
    assert current_handle == 'angusdoe'

    # handle_str will be invalid as it is greater than 20 characters
    handle_str = 'this_handle_will_be_too_long_to_work'
    result = requests.put(f"{url}/user/profile/sethandle", json={
        "token": token, 
        "handle_str": handle_str
    })
    payload = result.json()
    assert payload['code'] == 400    
