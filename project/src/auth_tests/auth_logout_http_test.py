'''
auth_logout_http_test.py

Fixtures:
    register_login: registers a user and logs that user in

Test Modules:
    test_unsuccessful_logout: tests loging out with invalid token
    test_empty_token: test loging out with empty token  
    test_successful_logout: test loging out with valid token                                                                                                                                                                                                                                                                                                                     
'''
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import pytest
import re
from subprocess         import Popen, PIPE
import signal
from time               import sleep
import requests
import json

from error              import AccessError, InputError
from helper             import token_validator, token_hash

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
   
    r = requests.post(f"{url}/auth/register", json={
        "email":"test@email.com", 
        "password": "password", 
        "name_first": "Angus", 
        "name_last": "Doe"
    })
    payload = r.json()

    r = requests.post(f"{url}/auth/login", json={
        'email': 'test@email.com', 
        'password': 'password'
    })
    payload = r.json()

    return payload

def test_unsuccessful_logout(url, register_login):
    token = token_hash(1)

    r = requests.post(f"{url}/auth/logout", json={
        'token': token
    })
    payload = r.json()

    assert payload == {'is_success' : False}

def test_empty_token(url, register_login):
    token = token_hash(1)

    r = requests.post(f"{url}/auth/logout", json={
        'token': token
    })
    payload = r.json()

    assert payload == {'is_success' : False}

def test_successful_logout(url, register_login):
    token = token_hash(0)

    r = requests.post(f"{url}/auth/logout", json={
        'token': token
    })
    payload = r.json()

    assert payload == {'is_success' : True}
