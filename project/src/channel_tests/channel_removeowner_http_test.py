import pytest
import re
import signal
import requests
from time           import sleep
from subprocess     import Popen, PIPE
import json
import urllib

from error          import InputError, AccessError
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

def test_invalid_token(url, register_login):
    user = register_login
    is_public = True
    # Creating a channel
    r_channel_create = requests.post(f"{url}/channels/create", json={
        'token': user['token'],
        'name': 'channel',
        'is_public': is_public
    })
    payload_c = r_channel_create.json()
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

    # Making the second user join the channel
    requests.post(f"{url}/channel/join", json={
        'token': payload['token'],
        'channel_id': payload_c['channel_id']
    })
    
    invalid_token = token_hash(1)
    r_channel_removeowner = requests.post(f"{url}/channel/removeowner", json={
        'token': invalid_token,
        'channel_id': payload_c['channel_id'],
        'u_id': payload['u_id']
    })
    payload = r_channel_removeowner.json()
    assert payload['code'] == 400

def test_invalid_channel_id(url, register_login):
    user = register_login
    is_public = True
    # Creating a channel
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

    user2 = requests.post(f"{url}/auth/login", json={
        'email': 'test2@email.com',
        'password': 'password2'
    })

    payload_u = user2.json()
    # Making the second user join the channel
    requests.post(f"{url}/channel/join", json={
        'token': payload_u['token'],
        'channel_id': payload['channel_id']
    })
    
    invalid_channel_id = -1
    r_channel_removeowner = requests.post(f"{url}/channel/removeowner", json={
        'token': user['token'],
        'channel_id': invalid_channel_id,
        'u_id': payload_u['u_id']
    })
    payload = r_channel_removeowner.json()
    assert payload['code'] == 400

def test_ivalid_u_id(url, register_login):
    user = register_login

    # Creating a channel
    r_channel_create = requests.post(f"{url}/channels/create", json={
        'token': user['token'],
        'name': 'channel',
        'is_public': True
    })
    payload = r_channel_create.json()
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
    payload_u = user2.json()
    # Making the second user join the channel
    requests.post(f"{url}/channel/join", json={
        'token': payload_u['token'],
        'channel_id': payload['channel_id']
    })
    
    invalid_u_id = -1
    r_channel_removeowner = requests.post(f"{url}/channel/removeowner", json={
        'token': user['token'],
        'channel_id': payload['channel_id'],
        'u_id': invalid_u_id
    })
    payload = r_channel_removeowner.json()
    assert payload['code'] == 400

# The user who is being removed with user id u_id is not an owner of the channel
def test_invalid_owner_remove_1(url, register_login):
    user = register_login
    is_public = True
    # Creating a channel
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
    user2 = requests.post(f"{url}/auth/login", json={
        'email': 'test2@email.com',
        'password': 'password2'
    })
    payload_u = user2.json()
    # Making the second user join the channel
    requests.post(f"{url}/channel/join", json={
        'token': payload_u['token'],
        'channel_id': payload['channel_id']
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
    payload_u = user3.json()

    # Making the third user join the channel
    requests.post(f"{url}/channel/join", json={
        'token': payload_u['token'],
        'channel_id': payload['channel_id']
    })

    r_channel_removeowner = requests.post(f"{url}/channel/removeowner", json={
        'token': payload_u['token'],
        'channel_id': payload['channel_id'],
        'u_id': payload_u['u_id']
    })
    payload = r_channel_removeowner.json()
    assert payload['code'] == 400

# The user who wants to remove an owner is not an owner of the channel
def test_invalid_owner_remove_2(url, register_login):
    user = register_login
    is_public = True

    # Creating a channel
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

    user2 = requests.post(f"{url}/auth/login", json={
        'email': 'test2@email.com',
        'password': 'password2'
    })
    payload_u2 = user2.json()

    # Making the second user join the channel
    requests.post(f"{url}/channel/join", json={
        'token': payload_u2['token'],
        'channel_id': payload['channel_id']
    })

    r_channel_removeowner = requests.post(f"{url}/channel/removeowner", json={
        'token': payload_u2['token'],
        'channel_id': payload['channel_id'],
        'u_id': user['u_id']
    })
    payload = r_channel_removeowner.json()
    assert payload['code'] == 400

def test_remove_owner_success(url, register_login):
    user = register_login
    is_public = True
    # Creating a channel
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

    user2 = requests.post(f"{url}/auth/login", json={
        'email': 'test2@email.com',
        'password': 'password2'
    })
    payload_u2 = user2.json()

    # Making the second user join the channel
    requests.post(f"{url}/channel/join", json={
        'token': payload_u2['token'],
        'channel_id': payload['channel_id']
    })

    # Making the second user the owner of the channel
    requests.post(f"{url}/channel/addowner", json={
        'token': user['token'],
        'channel_id': payload['channel_id'],
        'u_id': payload_u2['u_id']
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
    payload_u3 = user3.json()

    # Making the third user join the channel
    requests.post(f"{url}/channel/join", json={
        'token': payload_u3['token'],
        'channel_id': payload['channel_id']
    })

    requests.post(f"{url}/channel/removeowner", json={
        'token': user['token'],
        'channel_id': payload['channel_id'],
        'u_id': payload_u2['u_id']
    })

    queryString = urllib.parse.urlencode({
        'token': user['token'],
        'channel_id': payload['channel_id'],
    })
    r_channel_details = requests.get(f"{url}/channel/details?{queryString}")

    payload = r_channel_details.json()
    assert not payload['owner_members'][0]['u_id'] 

def test_flockr_owner(url, register_login):
    flockr_owner = register_login
    is_public = True
    # Creating a second user and making them the channel owner
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
    payload_u2 = user2.json()
    
    # Creating a channel
    r_channel_create = requests.post(f"{url}/channels/create", json={
        'token': payload_u2['token'],
        'name': 'channel',
        'is_public': is_public
    })
    payload = r_channel_create.json()

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
    payload_u3 = user3.json()

    # Making the third user join the channel
    requests.post(f"{url}/channel/join", json={
        'token': payload_u3['token'],
        'channel_id': payload['channel_id']
    })

    # Making the third user the owner of the channel
    requests.post(f"{url}/channel/addowner", json={
        'token': flockr_owner['token'],
        'channel_id': payload['channel_id'],
        'u_id': payload_u3['u_id']
    })

    requests.post(f"{url}/channel/removeowner", json={
        'token': flockr_owner['token'],
        'channel_id': payload['channel_id'],
        'u_id': payload_u3['u_id']
    })

    queryString = urllib.parse.urlencode({
        'token': payload_u2['token'],
        'channel_id': payload['channel_id'],
    })
    r_channel_details = requests.get(f"{url}/channel/details?{queryString}")

    payload = r_channel_details.json()
    assert len(payload['owner_members']) == 1
