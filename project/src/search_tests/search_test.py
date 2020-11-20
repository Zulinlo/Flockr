"""
search_test.py

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
from implement.auth           import auth_register, auth_login
from implement.channels       import channels_create
from implement.channel        import channel_join, channel_messages
from error          import AccessError, InputError
from implement.other          import clear, search
from implement.message        import message_send
from helper         import token_hash

@pytest.fixture
def channel_user():
    clear()
    auth_register("owner@email.com", "password", "Firstname", "Lastname")
    token = auth_login("owner@email.com", "password")
    public = True
    c_id = channels_create(token['token'], "Channel0", public)

    return {
        'u_id': token['u_id'], 
        'token': token['token'], 
        'c_id': c_id['channel_id'],
    }

@pytest.fixture
def send_messages(channel_user):
    owner = channel_user
    # Messages to be used in search
    message_send(owner['token'], owner['c_id'], "Channel0 - Message 0")
    message_send(owner['token'], owner['c_id'], "channel0 z Message 1!")
    message_send(owner['token'], owner['c_id'], "....................")

# Test Invalid Cases:
#####################################################################

# AccessError: token passed in does not refer to a valid user.
def test_invalid_token():
    query_str = "Query String"
    with pytest.raises(AccessError):
        search(token_hash(1), query_str)

# Assumption: Raise an InputError if the query string is empty
def test_empty_query_str(channel_user):
    owner = channel_user
    query_str_empty = ""
    with pytest.raises(InputError):
        search(owner['token'], query_str_empty)

# Assumption: Raise an InputError if the query string contains white space
def test_whitespace_query_str(channel_user):
    owner = channel_user
    query_str_space = "     "
    with pytest.raises(InputError):
        search(owner['token'], query_str_space)

# Assumption: Raise an AccessError when the user tries to search for 
#             messages but isn't part of any channels
def test_no_channels_joined():
    # Register a second user who is not part of the channel
    auth_register("user2@email.com", "password", "Firstname", "Lastname")
    user_2 = auth_login("user2@email.com", "password")

    query_str = "Query String"
    with pytest.raises(AccessError):
        search(user_2['token'], query_str)

# Scenario: user searches a joined channel but there are no matches 
#           related to the search (Raise InputError)
def test_no_matches(channel_user, send_messages):
    owner = channel_user

    query_str = "No matches related to search"
    with pytest.raises(InputError):
        search(owner['token'], query_str)

# Test Success Cases:
#####################################################################

# Assumption: uppercase and lowercase letters are treated as the same
#             in the search
def test_letter_matches(channel_user, send_messages):
    owner = channel_user

    message_0 = channel_messages(owner['token'], owner['c_id'], 0)['messages'][0]
    message_1 = channel_messages(owner['token'], owner['c_id'], 0)['messages'][1]

    query_str = "a"
    search_result = search(owner['token'], query_str)
    assert search_result == {'messages': [message_0, message_1]}
    
    query_str = "z"
    search_result = search(owner['token'], query_str)
    assert search_result == {'messages': [message_1]}

def test_symbol_matches(channel_user, send_messages):
    owner = channel_user
    message_0 = channel_messages(owner['token'], owner['c_id'], 0)['messages'][0]
    message_1 = channel_messages(owner['token'], owner['c_id'], 0)['messages'][1]

    query_str = "-"
    search_result = search(owner['token'], query_str)
    assert search_result == {'messages': [message_0]}

    query_str = "!"
    search_result = search(owner['token'], query_str)
    assert search_result == {'messages': [message_1]}

def test_number_matches(channel_user, send_messages):
    owner = channel_user
    message_0 = channel_messages(owner['token'], owner['c_id'], 0)['messages'][0]
    message_1 = channel_messages(owner['token'], owner['c_id'], 0)['messages'][1]

    query_str = "0"
    search_result = search(owner['token'], query_str)
    assert search_result == {'messages': [message_0, message_1]}

    query_str = "1"
    search_result = search(owner['token'], query_str)
    assert search_result == {'messages': [message_1]}

def test_word_matches(channel_user, send_messages):
    owner = channel_user
    message_0 = channel_messages(owner['token'], owner['c_id'], 0)['messages'][0]
    message_1 = channel_messages(owner['token'], owner['c_id'], 0)['messages'][1]

    query_str = "channel"
    search_result = search(owner['token'], query_str)
    assert search_result == {'messages': [message_0, message_1]}
    
    query_str = "message"
    search_result = search(owner['token'], query_str)
    assert search_result == {'messages': [message_0, message_1]}

def test_sentence_matches(channel_user, send_messages):
    owner = channel_user
    message_0 = channel_messages(owner['token'], owner['c_id'], 0)['messages'][0]
    message_1 = channel_messages(owner['token'], owner['c_id'], 0)['messages'][1]

    query_str = "Channel0 - Message"
    search_result = search(owner['token'], query_str)
    assert search_result == {'messages': [message_0]}

    query_str = "Message 1!"
    search_result = search(owner['token'], query_str)
    assert search_result == {'messages': [message_1]}

# Two channels are created which both contain messages
# Abbreviation: ch_0_ms_0 means channel_0_message_0
def test_multiple_channels(channel_user, send_messages):
    owner = channel_user

    ch_0_ms_0 = channel_messages(owner['token'], owner['c_id'], 0)['messages'][0]
    ch_0_ms_1 = channel_messages(owner['token'], owner['c_id'], 0)['messages'][1]

    # Create another channel which also contains messages
    public = True
    c_id_2 = channels_create(owner['token'], "Channel1", public)['channel_id']
    
    # Messages in Channel1 to be used in search
    message_send(owner['token'], c_id_2, "Channel1 - Message 0")
    message_send(owner['token'], c_id_2, "Channel1 - Message 1")
    
    ch_1_ms_0 = channel_messages(owner['token'], c_id_2, 0)['messages'][0]
    ch_1_ms_1 = channel_messages(owner['token'], c_id_2, 0)['messages'][1]

    query_str = "Channel0"
    search_result = search(owner['token'], query_str)
    assert search_result == {'messages': [ch_0_ms_0, ch_0_ms_1]}

    query_str = "Channel1"
    search_result = search(owner['token'], query_str)
    assert search_result == {'messages': [ch_1_ms_0, ch_1_ms_1]}
