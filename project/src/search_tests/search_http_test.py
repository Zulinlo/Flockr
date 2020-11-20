"""
search_http_test.py

Fixtures:
    channel_user: registers and logs in a user, then creates a channel with that user
    send_messages: owner from channel_user sends messages into the channel created

Test Modules:
    test_invalid_token: fail case where token does not match a valid user
    test__empty_query_str: fail case where query string is empty
    test_whitespace_query_str: fail case where query string is only white space
    test_no_channels_joined: fail case where user isn't in any channels
    test_no_matches: fail case where there are no matches to the search
    test_letter_matches: success case where upper and lower case letters match
    test_symbol_matches: success case where symbols match
    test_number_matches: success case where numbers match
    test_word_matches: success case where words match
    test_sentence_matches: success case where a sentence matches
    test_multiple_channels: success case where query search finds matches in multiple channels
"""
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

from error          import AccessError, InputError
from implement.other          import search
from helper         import token_hash

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
def channel_user(url):
    requests.delete(f"{url}/clear")

    requests.post(f"{url}/auth/register", json={
        'email': 'owner@email.com', 
        'password': 'password', 
        'name_first': 'Firstname', 
        'name_last': 'Lastname'
    })

    r = requests.post(f"{url}/auth/login", json={
        'email': 'owner@email.com', 
        'password': 'password'
    })
    owner = r.json()

    r = requests.post(f"{url}/channels/create", json={
        'token': owner['token'],
        'name': 'Channel0',
        'is_public': True
    })
    c_id = r.json()

    return {
        'u_id': owner['u_id'], 
        'token': owner['token'], 
        'c_id': c_id['channel_id'],
    }

@pytest.fixture
def send_messages(url, channel_user):
    owner = channel_user

    requests.post(f"{url}/message/send", json={
        'token': owner['token'],
        'channel_id': owner['c_id'],
        'message': "Channel0 - Message 0"
    })

    requests.post(f"{url}/message/send", json={
        'token': owner['token'],
        'channel_id': owner['c_id'],
        'message': "channel0 z Message 1!"
    })

    requests.post(f"{url}/message/send", json={
        'token': owner['token'],
        'channel_id': owner['c_id'],
        'message': "...................."
    })

'''Invalid Cases'''
# AccessError: token passed in does not refer to a valid user.
def test_invalid_token(url):
    invalid_token = token_hash(-1)

    queryString = urllib.parse.urlencode({
        'token': invalid_token,
        'query_str': "Query String"
    })
    r = requests.get(f"{url}/search?{queryString}")
    
    payload = r.json()
    assert payload['code'] == 400

# Assumption: Raise an InputError if the query string is empty
def test_empty_query_str(url, channel_user):
    owner = channel_user

    queryString = urllib.parse.urlencode({
        'token': owner['token'],
        'query_str': ""
    })
    r = requests.get(f"{url}/search?{queryString}")
    
    payload = r.json()
    assert payload['code'] == 400

# Assumption: Raise an InputError if the query string contains white space
def test_whitespace_query_str(url, channel_user):
    owner = channel_user

    queryString = urllib.parse.urlencode({
        'token': owner['token'],
        'query_str': "     "
    })
    r = requests.get(f"{url}/search?{queryString}")
    
    payload = r.json()
    assert payload['code'] == 400

# Assumption: Raise an AccessError when the user tries to search for 
#             messages but isn't part of any channels
def test_no_channels_joined(url):
    # Register a second user who is not part of the channel
    requests.post(f"{url}/auth/register", json={
        'email': 'user2@email.com', 
        'password': 'password', 
        'name_first': 'Firstname', 
        'name_last': 'Lastname'
    })

    r = requests.post(f"{url}/auth/login", json={
        'email': 'user2@email.com', 
        'password': 'password'
    })
    user_2 = r.json()

    queryString = urllib.parse.urlencode({
        'token': user_2['token'],
        'query_str': "Query String"
    })
    r = requests.get(f"{url}/search?{queryString}")

    payload = r.json()
    assert payload['code'] == 400

# Scenario: user searches a joined channel but there are no matches 
#           related to the search (Raise InputError)
def test_no_matches(url, channel_user, send_messages):
    owner = channel_user

    queryString = urllib.parse.urlencode({
        'token': owner['token'],
        'query_str': "No matches related to search"
    })
    r = requests.get(f"{url}/search?{queryString}")

    payload = r.json()
    assert payload['code'] == 400

'''Success Cases'''
# Assumption: uppercase and lowercase letters are treated as the same
#             in the search
def test_letter_matches(url, channel_user, send_messages):
    owner = channel_user

    queryString = urllib.parse.urlencode({
        'token': owner['token'],
        'channel_id': owner['c_id'],
        'start': 0
    })
    r = requests.get(f"{url}/channel/messages?{queryString}")
    message_0 = r.json()['messages'][0]

    queryString = urllib.parse.urlencode({
        'token': owner['token'],
        'channel_id': owner['c_id'],
        'start': 0
    })
    r = requests.get(f"{url}/channel/messages?{queryString}")
    message_1 = r.json()['messages'][1]

    queryString = urllib.parse.urlencode({
        'token': owner['token'],
        'query_str': "a"
    })
    r = requests.get(f"{url}/search?{queryString}")
    search_result = r.json()

    assert search_result == {'messages': [message_0, message_1]}

    queryString = urllib.parse.urlencode({
        'token': owner['token'],
        'query_str': "z"
    })
    r = requests.get(f"{url}/search?{queryString}")
        
    search_result = r.json()

    assert search_result == {'messages': [message_1]}

def test_symbol_matches(url, channel_user, send_messages):
    owner = channel_user

    queryString = urllib.parse.urlencode({
        'token': owner['token'],
        'channel_id': owner['c_id'],
        'start': 0
    })
    r = requests.get(f"{url}/channel/messages?{queryString}")
    message_0 = r.json()['messages'][0]
    
    queryString = urllib.parse.urlencode({
        'token': owner['token'],
        'channel_id': owner['c_id'],
        'start': 0
    })
    r = requests.get(f"{url}/channel/messages?{queryString}")
    message_1 = r.json()['messages'][1]

    queryString = urllib.parse.urlencode({
        'token': owner['token'],
        'query_str': "-"
    })
    r = requests.get(f"{url}/search?{queryString}")
    search_result = r.json()

    assert search_result == {'messages': [message_0]}

    queryString = urllib.parse.urlencode({
        'token': owner['token'],
        'query_str': "!"
    })
    r = requests.get(f"{url}/search?{queryString}")
    search_result = r.json()

    assert search_result == {'messages': [message_1]}

def test_number_matches(url, channel_user, send_messages):
    owner = channel_user

    queryString = urllib.parse.urlencode({
        'token': owner['token'],
        'channel_id': owner['c_id'],
        'start': 0
    })
    r = requests.get(f"{url}/channel/messages?{queryString}")
    message_0 = r.json()['messages'][0]

    queryString = urllib.parse.urlencode({
        'token': owner['token'],
        'channel_id': owner['c_id'],
        'start': 0
    })
    r = requests.get(f"{url}/channel/messages?{queryString}")
    message_1 = r.json()['messages'][1]

    queryString = urllib.parse.urlencode({
        'token': owner['token'],
        'query_str': "0"
    })
    r = requests.get(f"{url}/search?{queryString}")
    search_result = r.json()

    assert search_result == {'messages': [message_0, message_1]}

    queryString = urllib.parse.urlencode({
        'token': owner['token'],
        'query_str': "1"
    })
    r = requests.get(f"{url}/search?{queryString}")
    search_result = r.json()

    assert search_result == {'messages': [message_1]}

def test_word_matches(url, channel_user, send_messages):
    owner = channel_user

    queryString = urllib.parse.urlencode({
        'token': owner['token'],
        'channel_id': owner['c_id'],
        'start': 0
    })
    r = requests.get(f"{url}/channel/messages?{queryString}")
    message_0 = r.json()['messages'][0]

    queryString = urllib.parse.urlencode({
        'token': owner['token'],
        'channel_id': owner['c_id'],
        'start': 0
    })
    r = requests.get(f"{url}/channel/messages?{queryString}")
    message_1 = r.json()['messages'][1]

    queryString = urllib.parse.urlencode({
        'token': owner['token'],
        'query_str': "channel"
    })
    r = requests.get(f"{url}/search?{queryString}")
    search_result = r.json()

    assert search_result == {'messages': [message_0, message_1]}
    
    queryString = urllib.parse.urlencode({
        'token': owner['token'],
        'query_str': "message"
    })
    r = requests.get(f"{url}/search?{queryString}")
    search_result = r.json()

    assert search_result == {'messages': [message_0, message_1]}

def test_sentence_matches(url, channel_user, send_messages):
    owner = channel_user

    queryString = urllib.parse.urlencode({
        'token': owner['token'],
        'channel_id': owner['c_id'],
        'start': 0
    })
    r = requests.get(f"{url}/channel/messages?{queryString}")
    message_0 = r.json()['messages'][0]

    queryString = urllib.parse.urlencode({
        'token': owner['token'],
        'channel_id': owner['c_id'],
        'start': 0
    })
    r = requests.get(f"{url}/channel/messages?{queryString}")
    message_1 = r.json()['messages'][1]

    queryString = urllib.parse.urlencode({
        'token': owner['token'],
        'query_str': "Channel0 - Message"
    })
    r = requests.get(f"{url}/search?{queryString}")
    search_result = r.json()

    assert search_result == {'messages': [message_0]}

    queryString = urllib.parse.urlencode({
        'token': owner['token'],
        'query_str': "Message 1!"
    })
    r = requests.get(f"{url}/search?{queryString}")
    search_result = r.json()

    assert search_result == {'messages': [message_1]}

# Two channels are created which both contain messages
# Abbreviation: ch_0_ms_0 means channel_0_message_0
def test_multiple_channels(url, channel_user, send_messages):
    owner = channel_user

    queryString = urllib.parse.urlencode({
        'token': owner['token'],
        'channel_id': owner['c_id'],
        'start': 0
    })
    r = requests.get(f"{url}/channel/messages?{queryString}")
    ch_0_ms_0 = r.json()['messages'][0]

    queryString = urllib.parse.urlencode({
        'token': owner['token'],
        'channel_id': owner['c_id'],
        'start': 0
    })
    r = requests.get(f"{url}/channel/messages?{queryString}")
    ch_0_ms_1 = r.json()['messages'][1]

    # Create another channel which also contains messages
    r = requests.post(f"{url}/channels/create", json={
        'token': owner['token'],
        'name': 'Channel1',
        'is_public': True
    })
    c_id_2 = r.json()['channel_id']
    
    # Messages in Channel1 to be used in search
    requests.post(f"{url}/message/send", json={
        'token': owner['token'],
        'channel_id': c_id_2,
        'message': "Channel1 - Message 0"
    })

    requests.post(f"{url}/message/send", json={
        'token': owner['token'],
        'channel_id': c_id_2,
        'message': "Channel1 - Message 1"
    })
    
    queryString = urllib.parse.urlencode({
        'token': owner['token'],
        'channel_id': c_id_2,
        'start': 0
    })
    r = requests.get(f"{url}/channel/messages?{queryString}")
    ch_1_ms_0 = r.json()['messages'][0]

    queryString = urllib.parse.urlencode({
        'token': owner['token'],
        'channel_id': c_id_2,
        'start': 0
    })
    r = requests.get(f"{url}/channel/messages?{queryString}")
    ch_1_ms_1 = r.json()['messages'][1]
    
    queryString = urllib.parse.urlencode({
        'token': owner['token'],
        'query_str': "Channel0"
    })
    r = requests.get(f"{url}/search?{queryString}")
    search_result = r.json()
    
    assert search_result == {'messages': [ch_0_ms_0, ch_0_ms_1]}

    queryString = urllib.parse.urlencode({
        'token': owner['token'],
        'query_str': "Channel1"
    })
    r = requests.get(f"{url}/search?{queryString}")
    search_result = r.json()

    assert search_result == {'messages': [ch_1_ms_0, ch_1_ms_1]}
