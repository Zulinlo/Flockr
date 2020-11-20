"""
auth_register_http_test.py

Test Modules:
    test_valid_email: test registering user with valid email
    test_invalid_email_no_at: test when email entered has no '@'
    test_invalid_email_no_com: test when email entered has no ".com'
    test_email_exists: test when email entered already been registered
    test_pw_under_six: test when email entered under six characters
    test_invalid_firstname: test when firstname entered is empty
    test_valid_firstname_onechar: test firstname entered as one character
    test_invalid_firstname_long: test when firstname over 50 characters
    test_invalid_lastname_long: test when lastname over 50 characters
    test_valid_lastname_onechar: test lastname entered as one character
    test_invalid_lastname: test when lastname entered is one character
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import pytest
import re
import signal
import json
import requests

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

def test_valid_email(url):
    requests.delete(f"{url}/clear")
    result = requests.post(f"{url}/auth/register", json={
        "email":"test@email.com", 
        "password": "password", 
        "name_first": "Angus", 
        "name_last": "Doe"
    })
    token = token_hash(0)
    payload = result.json()
    assert payload == {
            'u_id': 0,
            'token': token,
    }
    result = requests.post(f"{url}/auth/register", json={
        "email": "test123123@email.com", 
        "password": "password", 
        "name_first": "Angus", 
        "name_last": "Doe"
    })
    token = token_hash(1)
    payload = result.json()
    assert payload == {
            'u_id': 1,
            'token': token,
    }

def test_invalid_email_no_at(url):
    requests.delete(f"{url}/clear")
    result = requests.post(f"{url}/auth/register", json={
        "email":"testemail.com", 
        "password": "password", 
        "name_first": "Angus", 
        "name_last": "Doe"
    })
    payload = result.json()
    assert payload['code'] == 400

def test_invalid_email_no_com(url):
    requests.delete(f"{url}/clear")
    result = requests.post(f"{url}/auth/register", json={
        "email": "testemail@gmail", 
        "password": "password", 
        "name_first": "Angus", 
        "name_last": "Doe"
    })
    payload = result.json()
    assert payload['code'] == 400

def test_email_exists(url):
    requests.post(f"{url}/auth/register", json={
        "email":"test@email.com", 
        "password": "password", 
        "name_first": "Angus", 
        "name_last": "Doe"
    })
    result = requests.post(f"{url}/auth/register", json={
        "email":"test@email.com", 
        "password": "password", 
        "name_first": "Angus", 
        "name_last": "Doe 2nd"
    })
    payload = result.json()
    assert payload['code'] == 400

def test_pw_under_six(url):
    requests.delete(f"{url}/clear")
    result = requests.post(f"{url}/auth/register", json={
        "email":"test@email.com", 
        "password": "pw", 
        "name_first": "Angus", 
        "name_last": "Doe"
    })
    payload = result.json()
    assert payload['code'] == 400

def test_invalid_firstname(url):
    requests.delete(f"{url}/clear")
    result = requests.post(f"{url}/auth/register", json={
        "email":"test@email.com", 
        "password": "password", 
        "name_first": "", 
        "name_last": "Doe"
    })
    payload = result.json()
    assert payload['code'] == 400

def test_valid_firstname_onechar(url):
    requests.delete(f"{url}/clear")
    result = requests.post(f"{url}/auth/register", json={
        "email":"test@email.com", 
        "password": "password", 
        "name_first": "A", 
        "name_last": "Doe"
    })
    token = token_hash(0)
    payload = result.json()
    assert payload == {
            'u_id': 0,
            'token': token,
    }

def test_invalid_firstname_long(url):
    requests.delete(f"{url}/clear")
    long_name = "This is over 50 charactersThis is over 50characters"
    result = requests.post(f"{url}/auth/register", json={
        "email":"test@email.com", 
        "password": "password", 
        "name_first": long_name,
        "name_last": "Doe"
    })
    payload = result.json()
    assert payload['code'] == 400

def test_invalid_lastname_long(url):
    requests.delete(f"{url}/clear")
    long_name = "This is over 50 charactersThis is over 50characters"
    result = requests.post(f"{url}/auth/register", json={
        "email":"test@email.com", 
        "password": "password", 
        "name_first": "Angus", 
        "name_last": long_name
    })
    payload = result.json()
    assert payload['code'] == 400

def test_valid_lastname_onechar(url):
    requests.delete(f"{url}/clear")
    result = requests.post(f"{url}/auth/register", json={
        "email":"test@email.com", 
        "password": "password", 
        "name_first": "Angus", 
        "name_last": "D"
    })
    token = token_hash(0)
    payload = result.json()
    assert payload == {
            'u_id': 0,
            'token': token,
    }

def test_invalid_lastname(url):
    requests.delete(f"{url}/clear")
    result = requests.post(f"{url}/auth/register", json={
        "email":"test@email.com", 
        "password": "password", 
        "name_first": "Angus", 
        "name_last": ""
    })
    payload = result.json()
    assert payload['code'] == 400
