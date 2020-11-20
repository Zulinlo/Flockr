"""
user_profile_setname_http_test.py

Fixtures:
    register_login: creates a user and logs into that user

Test Modules:
    test_invalid_token: tests for invalid token
    test_invalid_first_name_too_long: tests edge case for when the first name is 51 characters long
    test_invalid_first_name_too_short: tests edge case for when the first name is 0 characters long
    test_invalid_last_name_too_long: tests edge case for when the last name is 51 characters long
    test_invalid_last_name_too_short: tests edge case for when the last name is 0 characters long
    test_valid_setname: tests for when names are valid and passes
"""
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
        "email":"example@gmail.com", 
        "password": "password", 
        "name_first": "Angus", 
        "name_last": "Doe"
    })

    result = requests.post(f"{url}/auth/login", json={
        "email":"example@gmail.com", 
        "password": "password"
    })
    payload = result.json()
    return payload

def test_invalid_token(url, register_login):
    name_first = 'Validfirst'
    name_last = 'Validlast'

    token = token_hash(2)
    result = requests.put(f"{url}/user/profile/setname", json={
        "token": token, 
        "name_first": name_first,
        "name_last": name_last
    })  
    payload = result.json()
    assert payload['code'] == 400

def test_invalid_first_name_too_long(url, register_login):
    user = register_login

    name_first = 'Abcdefghijklmnopqrstuvwxyasdpoeowoqowowowowowowowow'
    name_last = 'Validlast'
    token = user['token']

    result = requests.put(f"{url}/user/profile/setname", json={
        "token": token, 
        "name_first": name_first,
        "name_last": name_last
    })
    payload = result.json()
    assert payload['code'] == 400

def test_invalid_first_name_too_short(url, register_login):
    user = register_login

    name_first = ''
    name_last = 'Validlast'
    token = user['token']

    result = requests.put(f"{url}/user/profile/setname", json={
        "token": token, 
        "name_first": name_first,
        "name_last": name_last
    })
    payload = result.json()
    assert payload['code'] == 400

def test_invalid_last_name_too_long(url, register_login):
    user = register_login

    name_first = 'Validfirst'
    name_last = 'Abcdefghijklmnopqrstuvwxyasdpoeowoqowowowowowowowow'
    token = user['token']

    result = requests.put(f"{url}/user/profile/setname", json={
        "token": token, 
        "name_first": name_first,
        "name_last": name_last
    })
    payload = result.json()
    assert payload['code'] == 400

def test_invalid_last_name_too_short(url, register_login):
    user = register_login
    name_first = 'Validfirst'
    name_last = ''
    token = user['token']

    result = requests.put(f"{url}/user/profile/setname", json={
        "token": token, 
        "name_first": name_first,
        "name_last": name_last
    })
    payload = result.json()
    assert payload['code'] == 400

def test_valid_setname(url, register_login):
    requests.post(f"{url}/auth/register", json={
        "email":"user@email.com", 
        "password": "password", 
        "name_first": "John", 
        "name_last": "Boo"
    })

    result = requests.post(f"{url}/auth/login", json={
        "email":"user@email.com", 
        "password": "password"
    })
    user = result.json()

    name_first = 'Second'
    name_last = 'Boe'
    token = user['token']
    u_id = user['u_id']

    requests.put(f"{url}/user/profile/setname", json={
        "token": token, 
        "name_first": name_first,
        "name_last": name_last
    })
    
    queryString = urllib.parse.urlencode({
        "token": token, 
        "u_id": u_id
    })
    changed_user_info = requests.get(f"{url}/user/profile?{queryString}")

    profile = changed_user_info.json()['user']

    assert name_first == profile['name_first']
    assert name_last == profile['name_last']
