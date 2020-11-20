'''
user_profile_setemail_http_test.py

Fixtures:
    register_login: registers and logs in a user and returns their token

Test Modules:
    test_incorrect_email: fail case for the new email being invalid due to no @
    test_invalid_email_no_dot: fail case for the new email being invalid due to no .
    test_preexisting_email: fail case for when the email is the user's prexisting email
    test_diff_user_existing_email: fail case for when another user is already using that email
    test_successful_edit: success case for valid update to email  
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

'''Test Invalid Cases:'''
# Testing with an incorrrect email due to no @, should raise InputError
def test_incorrect_email(url, register_login):
    user = register_login
    token = user["token"]
    incorrect_email = "incorrectemailgmail.com"
    result = requests.put(f"{url}/user/profile/setemail", json={
        "token": token, 
        "email": incorrect_email
    })
    payload = result.json()
    assert payload['code'] == 400

# Testing with an invalid email, with no dot, should raise InputError
def test_invalid_email_no_dot(url, register_login):
    user = register_login
    token = user["token"]
    incorrect_email = "invalid@usergmailcom"
    result = requests.put(f"{url}/user/profile/setemail", json={
        "token": token, 
        "email": incorrect_email
    })
    payload = result.json()
    assert payload['code'] == 400

# Testing with the exact email, cannot change the email to a preexisting email, should raise InputError
def test_preexisting_email(url, register_login):
    user = register_login
    token = user["token"]
    incorrect_email = "test@gmail.com"
    result = requests.put(f"{url}/user/profile/setemail", json={
        "token": token, 
        "email": incorrect_email
    })
    payload = result.json()
    assert payload['code'] == 400

'''Test Success Cases'''
# Testing with a valid and correct email, checking that it should be correct
def test_valid_email(url, register_login):
    user = register_login
    token = user["token"]
    assert user == {
        'u_id': 1,
        'token': token,
    }

# Testing for assertion if the original email was valid and can change to a valid email
def test_successful_edit(url, register_login):
    user = register_login
    token = user["token"]
    u_id = user["u_id"]

    valid_email = "newemail@gmail.com"
    requests.put(f"{url}/user/profile/setemail", json={
        "token": token, 
        "email": valid_email
    })
    token = token_hash(1)

    queryString = urllib.parse.urlencode({
        "token": token, 
        "u_id": u_id
    })
    result = requests.get(f"{url}/user/profile?{queryString}")

    new_email = result.json()['user']['email']
    assert new_email == valid_email
