"""
auth_passwordreset_request_http_test.py

Fixtures:
    register: creates two users but does not log them in.

Test Modules:
    test_valid_user: success case for when email corresponds with registered user
    test_valid_user2: success case for when email corresponds with registered user
    test_invalid_user: fail case for when email doesn't correspond with registered user
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import pytest
import re
import signal
import json
import requests

from helper     import token_hash
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
def register(url):
    requests.delete(f"{url}/clear")
    # Fixture registers a user but does not log them in
    # No return value
    # Create dummy users for email testing
    
    requests.post(f"{url}/auth/register", json={
        "email":"test@gmail.com", 
        "password": "password", 
        "name_first": "Angus", 
        "name_last": "Doe"
    })

    requests.post(f"{url}/auth/register", json={
        "email":"test2@gmail.com", 
        "password": "password", 
        "name_first": "Angus", 
        "name_last": "Boe"
    })
    
def test_valid_user(url, register):
    requests.delete(f"{url}/clear")

    # Request always returns {} but email with code will be sent
    result = requests.post(f"{url}/auth/passwordreset/request", json={
        "email":"test@gmail.com", 
    })
    payload = result.json()
    assert payload == {}

def test_valid_user2(url, register):
    requests.delete(f"{url}/clear")

    # Request always returns {} but email with code will be sent
    result = requests.post(f"{url}/auth/passwordreset/request", json={
        "email":"test2@gmail.com", 
    })
    payload = result.json()
    assert payload == {}

def test_invalid_user(url, register):
    requests.delete(f"{url}/clear")
    # Setting up valid users to request a password reset 
    register

    # Request always returns {} but email won't be sent
    result = requests.post(f"{url}/auth/passwordreset/request", json={
        "email":"invalid@gmail.com", 
    })
    payload = result.json()
    assert payload == {}

def test_invalid_user2(url, register):
    requests.delete(f"{url}/clear")
    # Setting up valid users to request a password reset 
    register

    # Request always returns {} but email won't be sent
    result = requests.post(f"{url}/auth/passwordreset/request", json={
        "email":"doesntexist@gmail.com", 
    })
    payload = result.json()
    assert payload == {}

