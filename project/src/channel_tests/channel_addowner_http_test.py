'''
channel_addowner_http_test.py

Fixtures:
    register_login: registers a user and logs that user in

Test Modules:
    test_invalid_token: tests when token doesn't match users token
    test_invalid_channel_id: tests when channel_id doesn't exist
    test_invalid_u_id: tests when u_id doesn't refer to a valid user                                                                                                                                                                                    
    test_user_already_owner: tests when user to be owner is already an owner                                                                                                                                                          
    test_test_invalid_owner_add: tests when authorised user is not an owner, but is trying to make someone else an owner.                                                                                                                                                                           
    test_add_owner_success: tests success case where ownder adds a valid user.
'''
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import pytest
import re
from subprocess     import Popen, PIPE
import signal
from time           import sleep
import requests
import json
import urllib

from error          import InputError, AccessError
from implement.other          import clear
from implement.auth import auth_register, auth_login
from implement.channels       import channels_create, channels_listall
from implement.channel        import channel_details
from helper         import token_hash

# Use this fixture to get the URL of the server.
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
    requests.post(f"{url}/auth/register", json={
        "email": "test@email.com",
        "password": "password",
        "name_first": "Richard",
        "name_last": "Shen"
        })

    r = requests.post(f"{url}/auth/login", json={
        'email': 'test@email.com',
        'password': 'password'
    })
    payload = r.json()

    return payload

# Testing if the token is invalid or not
def test_invalid_token(url, register_login):
    is_public = True
    invalid_token = token_hash(1)
    r_channel_create = requests.post(f"{url}/channels/create", json={
        'token': invalid_token,
        'name': 'channel',
        'is_public': is_public
    })
    payload = r_channel_create.json()
    assert payload['code'] == 400

# Testing if the channel_id is invalid or not
def test_invalid_channel_id(url, register_login):
    user = register_login
    is_public = True
    # Creating the channel 
    r_channel_create = requests.post(f"{url}/channels/create", json={
        'token': user['token'],
        'name': 'channel',
        'is_public': is_public
    })
    payload = r_channel_create.json()
    # Creating a second user
    requests.post(f"{url}/auth/register", json={
        "email": "test2@email.com",
        "password": "password2",
        "name_first": "Richard2",
        "name_last": "Shen2"
    })
    r = requests.post(f"{url}/auth/login", json={
        'email': 'test2@email.com',
        'password': 'password2'
    })
    user_2 = r.json()
    invalid_channel_id = -1
    r_channel_addowner = requests.post(f"{url}/channel/addowner", json={
        'token': user['token'],
        'channel_id': invalid_channel_id,
        'u_id': user_2['u_id']
    })
    payload = r_channel_addowner.json()
    assert payload['code'] == 400

# Testing if the u_id refers to a valid user or not
def test_invalid_u_id(url, register_login):
    user = register_login
    is_public = True
    r_channel_create = requests.post(f"{url}/channels/create", json={
        'token': user['token'],
        'name': 'channel',
        'is_public': is_public
    })
    payload = r_channel_create.json()
    invalid_u_id = -1
    r_channel_addowner = requests.post(f"{url}/channel/addowner", json={
        'token': user['token'],
        'channel_id': payload['channel_id'],
        'u_id': invalid_u_id
    })
    payload1 = r_channel_addowner.json()
    assert payload1['code'] == 400
# Testing if the user is already an owner or not
def test_user_already_owner(url, register_login):
    user = register_login
    is_public = True
    r_channel_create = requests.post(f"{url}/channels/create", json={
        'token': user['token'],
        'name': 'channel',
        'is_public': is_public
    })
    payload = r_channel_create.json()
    # Calling channel addowner with their own u_id, will not work since
    # they are already an owner
    r_channel_addowner = requests.post(f"{url}/channel/addowner", json={
        'token': user['token'],
        'channel_id': payload['channel_id'],
        'u_id': user['u_id']
    })
    payload = r_channel_addowner.json()
    assert payload['code'] == 400

# Authorised user is not an owner, but is trying to make someone else an owner
def test_invalid_owner_add(url, register_login):
    user = register_login
    is_public = True
    # Creating the channel
    r_channel_create = requests.post(f"{url}/channels/create", json={
        'token': user['token'],
        'name': 'channel',
        'is_public': is_public
    })
    payload = r_channel_create.json()

    channel_id = payload['channel_id']
    # Creating a second user
    requests.post(f"{url}/auth/register", json={
        "email": "test2@email.com",
        "password": "password2",
        "name_first": "Richard2",
        "name_last": "Shen2"
        })
    user2 = requests.post(f"{url}/auth/login", json={
        'email': 'test2@email.com',
        'password': 'password2'
    })
    payload1 = user2.json()

    # Making the second user join the channel
    requests.post(f"{url}/channel/join", json={
        'token': payload1['token'],
        'channel_id': channel_id
    })

    # Creating a third user
    requests.post(f"{url}/auth/register", json={
        "email": "test3@email.com",
        "password": "password3",
        "name_first": "Richard3",
        "name_last": "Shen3"
        })
    user3 = requests.post(f"{url}/auth/login", json={
        'email': 'test3@email.com',
        'password': 'password3'
    })
    payload2 = user3.json()

    # Making the third user join the channel
    requests.post(f"{url}/channel/join", json={
        'token': payload2['token'],
        'channel_id': channel_id
    })
    # Calling channel addowner, but should not work since the token of the user
    # is not authorised, they are not the owner of the channel, hence, no permission
    requests.post(f"{url}/channel/addowner", json={
        'token': payload1['token'],
        'channel_id': channel_id,
        'u_id': payload2['u_id']
    })

    queryString = urllib.parse.urlencode({
        'token': user['token'],
        'channel_id': channel_id
    })
    r_channel_details = requests.get(f"{url}/channel/details?{queryString}")
    payload3 = r_channel_details.json()
    
    # If channel addowner was not successful, there would only be one owner_member
    # in channel details, hence using len to assert it equal to 1
    assert len(payload3['owner_members']) == 1

# Testing if the owner can add a member as an owner successfuly
def test_add_owner_success(url, register_login):
    user = register_login
    is_public = True
    r_channel_create = requests.post(f"{url}/channels/create", json={
        'token': user['token'],
        'name': 'channel',
        'is_public': is_public
    })
    payload = r_channel_create.json()
    channel_id = payload['channel_id']
    # Creating a second user
    requests.post(f"{url}/auth/register", json={
        "email": "test2@email.com",
        "password": "password2",
        "name_first": "Richard2",
        "name_last": "Shen2"
        })
    user2 = requests.post(f"{url}/auth/login", json={
        'email': 'test2@email.com',
        'password': 'password2'
    })
    payload2 = user2.json()

    # Making the second user join the channel
    requests.post(f"{url}/channel/join", json={
        'token': payload2['token'],
        'channel_id': channel_id
    })

    requests.post(f"{url}/channel/addowner", json={
        'token': user['token'],
        'channel_id': payload['channel_id'],
        'u_id': payload2['u_id']
    })

    queryString = urllib.parse.urlencode({
        'token': user['token'],
        'channel_id': channel_id
    })
    r_channel_details = requests.get(f"{url}/channel/details?{queryString}")
    payload3 = r_channel_details.json()

    # If channel addowner was successful, there would be two owner_members
    # in channel details, hence using len to assert it equal to 2
    # Then also testing if the u_id in owner_members is the same as the newly
    # admitted owner's u_id
    assert len(payload3['owner_members']) == 2
    assert payload3['owner_members'][1]['u_id'] == payload2['u_id']

def test_is_flockr_owner(url, register_login):
    # First user to be registered is the official flockr owner,
    # They have any permissions but are not necessarily in owner_members
    # they juhst have the same permissions
    flockr_owner = register_login
    flockr_token = flockr_owner['token']

    # Creating a second user
    requests.post(f"{url}/auth/register", json={
        "email": "test2@email.com",
        "password": "password2",
        "name_first": "Richard2",
        "name_last": "Shen2"
        })
    user2 = requests.post(f"{url}/auth/login", json={
        'email': 'test2@email.com',
        'password': 'password2'
    })
    payload = user2.json()

    is_public = True
    r_channel_create = requests.post(f"{url}/channels/create", json={
        'token': payload['token'],
        'name': 'channel',
        'is_public': is_public
    })
    payload1 = r_channel_create.json()
    channel_id = payload1['channel_id']

    # Creating a third user
    requests.post(f"{url}/auth/register", json={
        "email": "test3@email.com",
        "password": "password3",
        "name_first": "Richard3",
        "name_last": "Shen3"
        })
    user3 = requests.post(f"{url}/auth/login", json={
        'email': 'test3@email.com',
        'password': 'password3'
    })
    payload2 = user3.json()

    # Making the third user join the channel
    requests.post(f"{url}/channel/join", json={
        'token': payload2['token'],
        'channel_id': channel_id
    })

    requests.post(f"{url}/channel/addowner", json={
        'token': flockr_token,
        'channel_id': channel_id,
        'u_id': payload2['u_id']
    })

    queryString = urllib.parse.urlencode({
        'token': payload['token'],
        'channel_id': payload1['channel_id']
    })
    r_channel_details = requests.get(f"{url}/channel/details?{queryString}")

    payload3 = r_channel_details.json()
    # If channel addowner was successful, there would be two owner_members
    # in channel details, hence using len to assert it equal to 2
    # Then also testing if the u_id in owner_members is the same as the newly
    # admitted owner's u_id
    assert len(payload3['owner_members']) == 2
    assert payload3['owner_members'][1]['u_id'] == payload2['u_id']
