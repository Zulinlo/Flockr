'''
auth_login_http_test.py

Test Modules:
    test_auth_valid_login: tests loging in user with valid username and password
    test_auth_invalid_login_email_no_at: test when email entered has no '@'  
    test_auth_invalid_login_email_no_dot: test when email entered has no '.'                                                                                                                                                                                  
    test_auth_invalid_login_email_not_registered: test when email entered not been registered                                                                                                                                                      
    test_auth_invalid_login_wrong_password: test incorrect password entered                                                                                                                                                                          
'''
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import pytest
import re
from subprocess import Popen, PIPE
import signal
from time import sleep
import requests
import json

from error          import InputError
from helper         import token_hash, password_hash

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

# email, password
def test_auth_valid_login(url):
    requests.delete(f"{url}/clear")
    requests.post(f"{url}/auth/register", json={
        'email': 'testemail@gmail.com', 
        'password': 'password', 
        'name_first': 'John', 
        'name_last': 'Doe'
    })
    
    r = requests.post(f"{url}/auth/login", json={
        'email': 'testemail@gmail.com', 
        'password': 'password'
    })

    token = token_hash(0)

    payload = r.json()
    assert payload == {
        'u_id': 0, 
        'token': token
    }

def test_auth_invalid_login_email_no_at(url):
    requests.delete(f"{url}/clear")
    r = requests.post(f"{url}/auth/login", json={
        'email': 'testemail.com', 
        'password': 'password'
    })
    payload = r.json()
    assert payload['code'] == 400

def test_auth_invalid_login_email_no_dot(url):
    requests.delete(f"{url}/clear")
    r = requests.post(f"{url}/auth/login", json={
        'email': 'testemail@gmail', 
        'password': 'password'
    })
    payload = r.json()
    assert payload['code'] == 400

def test_auth_invalid_login_email_not_registered(url):
    requests.delete(f"{url}/clear")
    r = requests.post(f"{url}/auth/login", json={
        'email': 'notregistered@gmail.com', 
        'password': 'password'
    })
    payload = r.json()
    assert payload['code'] == 400

def test_auth_invalid_login_wrong_password(url):
    requests.delete(f"{url}/clear")
    requests.post(f"{url}/auth/register", json={
        'email': 'testemail2@gmail.com', 
        'password': 'password', 
        'name_first': 'Alan', 
        'name_last': 'Doe'
    })

    r = requests.post(f"{url}/auth/login", json={
        'email': 'testemail2@gmail.com', 
        'password': 'wrongpassword'
    })
    payload = r.json()
    assert payload['code'] == 400
