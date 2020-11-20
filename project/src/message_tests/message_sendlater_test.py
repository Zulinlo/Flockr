'''
message_sendlater_test.py

Fixtures:
    channel_with_user: registers and logs in a user, and then creates a public channel
    get_current_time: returns the current date and time as a timestamp

Test Modules:
    test_message_sendlater_success: success case for messages being sent at correct time
    def test_message_sendtwolater_success: success case for two identical messages queued for same time having distinct message_id's
    test_message_1000: success case at max character limit
    test_multiple_messages: success case with multiple messages queued up at the same time
    test_invalid_token: fail case for invalid token
    test_invalid_channel_id: fail case for invalid channel id
    test_invalid_message_empty: fail case for empty message
    test_invalid_message_spaces: fail case for message only containing spaces
    test_invalid_message_1001: fail case for exceeding max character limit in message
    test_invalid_sender: fail case for user attempting to message a channel they're not in
    test_invalid_time: fail case for user scheduling a message for the past
'''
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import pytest
from implement.message    import message_sendlater
from error      import AccessError, InputError
from implement.other      import clear
from implement.auth       import auth_register, auth_login
from implement.channels   import channels_create
from implement.channel    import channel_messages
from datetime   import datetime, timezone
from time       import sleep
from helper     import token_hash


# Arguments: token, channel_id, message, time_sent
# Assumptions:
# - A user cannot send empty messages such as "" or "  "
# - The sender has to be apart of the channel to send a message
# - A user can send messages to a channel which only contains themselves in it.
# - The time when the message is scheduled to be sent must be in the future

@pytest.fixture
def channel_with_user():
    # A user is registered, logged in and owns a channel
    clear()
    auth_register("owner@email.com", "password", "Firstname", "Lastname")
    token = auth_login("owner@email.com", "password")
    public = True
    c_id = channels_create(token['token'], "Channel", public)

    return {
        'u_id': token['u_id'], 
        'token': token['token'], 
        'c_id': c_id['channel_id'],
    }

@pytest.fixture
def get_current_time():
    # The current time needs to be obtained in order to compare successful data
    current_time = datetime.utcnow()
    timestamp = int(current_time.replace(tzinfo=timezone.utc).timestamp())
    return timestamp


# Successful Test Cases:
#####################################################################

def test_message_sendlater_success(channel_with_user, get_current_time):
    sender = channel_with_user
    current_timestamp = get_current_time
    later_timestamp = current_timestamp + 3
    even_later_timestamp = current_timestamp + 5
   
    # Ensure there's no messages in the channel to begin with
    assert not channel_messages(sender['token'], sender['c_id'], 0)['messages']

    # Queue up multiple message
    message_sendlater(sender['token'], sender['c_id'], "Test Message 1", later_timestamp)
    message_sendlater(sender['token'], sender['c_id'], "Test Message 2", even_later_timestamp)
    
    # Check that no messages have been sent yet
    assert not channel_messages(sender['token'], sender['c_id'], 0)['messages']
    
    # Wait 3 seconds before checking if first message has been sent
    sleep(3)
    messages = channel_messages(sender['token'], sender['c_id'], 0)['messages']
    
    assert messages == [
        {
            'message_id': 0, 
            'u_id': 0, 
            'message': 'Test Message 1', 
            'time_created': later_timestamp,
            'reacts': [
                {
                    'react_id': 0,
                    'u_ids': [],
                    'is_this_user_reacted': False,
                }
            ],
            'is_pinned': False,
        },
    ]
    # Wait another 2 seconds to see if second message has been sent
    sleep(2)
    messages = channel_messages(sender['token'], sender['c_id'], 0)['messages']
    assert messages == [
        {
            'message_id': 0, 
            'u_id': 0, 
            'message':'Test Message 1', 
            'time_created': later_timestamp,
            'reacts': [
                {
                    'react_id': 0,
                    'u_ids': [],
                    'is_this_user_reacted': False,
                }
            ],
            'is_pinned': False,
        },
        {
            'message_id': 1, 
            'u_id': 0, 
            'message': 'Test Message 2', 
            'time_created': even_later_timestamp,
            'reacts': [
                {
                    'react_id': 0,
                    'u_ids': [],
                    'is_this_user_reacted': False,
                }
            ],
            'is_pinned': False,
        },
    ]

def test_message_sendtwolater_success(channel_with_user, get_current_time):
    sender = channel_with_user
    current_timestamp = get_current_time
    later_timestamp = current_timestamp + 3
   
    # Ensure there's no messages in the channel to begin with
    assert not channel_messages(sender['token'], sender['c_id'], 0)['messages']

    # Queue up multiple messages which are the same
    message_sendlater(sender['token'], sender['c_id'], "Test Message", later_timestamp)
    message_sendlater(sender['token'], sender['c_id'], "Test Message", later_timestamp)
    
    # Check that no messages have been sent yet
    assert not channel_messages(sender['token'], sender['c_id'], 0)['messages']
    
    # Wait 4 seconds (buffer time) before checking if both messages were sent
    # with distinct message_id
    sleep(4)
    messages = channel_messages(sender['token'], sender['c_id'], 0)['messages']
    print(messages)
    assert messages == [
        {
            'message_id': 0, 
            'u_id': 0, 
            'message':'Test Message', 
            'time_created': later_timestamp,
            'reacts': [
                {
                    'react_id': 0,
                    'u_ids': [],
                    'is_this_user_reacted': False,
                }
            ],
            'is_pinned': False,
        },
        {
            'message_id': 1, 
            'u_id': 0, 
            'message': 'Test Message', 
            'time_created': later_timestamp,
            'reacts': [
                {
                    'react_id': 0,
                    'u_ids': [],
                    'is_this_user_reacted': False,
                }
            ],
            'is_pinned': False,
        },
    ]

def test_message_1000(channel_with_user, get_current_time):
    sender = channel_with_user
    current_timestamp = get_current_time
    later_timestamp = current_timestamp + 3
    valid_message = "*" * 1000

    # Queue up the message to be sent later
    message_sendlater(sender['token'], sender['c_id'], valid_message, later_timestamp)

    # Check that no messages have been sent yet
    assert not channel_messages(sender['token'], sender['c_id'], 0)['messages']
    
    # Wait 5 seconds to see if messages have been sent (including buffer time)
    sleep(5)
    messages = channel_messages(sender['token'], sender['c_id'], 0)['messages']
    assert messages == [
        {
            'message_id': 0, 
            'u_id': 0, 
            'message': valid_message, 
            'time_created': later_timestamp,
            'reacts': [
                {
                    'react_id': 0,
                    'u_ids': [],
                    'is_this_user_reacted': False,
                }
            ],
            'is_pinned': False,
        },
    ]

# Ensure that the message_id is unique, even across channels
def test_multiple_channels(channel_with_user, get_current_time):
    sender = channel_with_user
    current_timestamp = get_current_time
    later_timestamp = current_timestamp + 3

    # Ensure there's no messages in the channel to begin with
    assert not channel_messages(sender['token'], sender['c_id'], 0)['messages']

    # Send the first message to the first channel
    message_sendlater(sender['token'], sender['c_id'], "Test Message 1", later_timestamp)
    
    # Check that no messages have been sent yet in first channel
    assert not channel_messages(sender['token'], sender['c_id'], 0)['messages']

    # Create second channel
    public = True
    channel_2 = channels_create(sender['token'], "Channel 2", public)['channel_id']

    # Send the second message in the second channel
    message_sendlater(sender['token'], channel_2, "Test Message 2", later_timestamp)
    
    # Check that no messages have been sent yet in the second channel
    assert not channel_messages(sender['token'], channel_2, 0)['messages']

    # Wait 5 seconds to see if messages have been sent (additional buffer time)
    sleep(5)
    messages = channel_messages(sender['token'], sender['c_id'], 0)['messages']
    messages2 = channel_messages(sender['token'], channel_2, 0)['messages']
    assert messages == [
        {
            'message_id': 0, 
            'u_id': 0, 
            'message': 'Test Message 1', 
            'time_created': later_timestamp,
            'reacts': [
                {
                    'react_id': 0,
                    'u_ids': [],
                    'is_this_user_reacted': False,
                }
            ],
            'is_pinned': False,
        },
    ]

    assert messages2 == [
        {
            'message_id': 1, 
            'u_id': 0, 
            'message': 
            'Test Message 2', 
            'time_created': later_timestamp,
            'reacts': [
                {
                    'react_id': 0,
                    'u_ids': [],
                    'is_this_user_reacted': False,
                }
            ],
            'is_pinned': False,
        },
    ]



# Test Invalid Cases:
######################################################

# AccessError: token passed in does not refer to a valid user.
def test_invalid_token(channel_with_user, get_current_time):
    sender = channel_with_user
    current_timestamp = get_current_time
    later_timestamp = current_timestamp + 3
    with pytest.raises(AccessError):
        message_sendlater(token_hash(-1), sender['c_id'], "Test Message", later_timestamp)

# InputError: channel_id does not refer to a valid channel.
def test_invalid_channel_id(channel_with_user, get_current_time):
    sender = channel_with_user
    current_timestamp = get_current_time
    later_timestamp = current_timestamp + 3
    invalid_c_id = -1
    with pytest.raises(InputError):
        message_sendlater(sender['token'], invalid_c_id, "Test Message", later_timestamp)

# InputError: Cannot send empty messsages
def test_invalid_message_empty(channel_with_user, get_current_time):
    sender = channel_with_user
    current_timestamp = get_current_time
    later_timestamp = current_timestamp + 3
    empty_message = ""
    with pytest.raises(InputError):
        message_sendlater(sender['token'], sender['c_id'], empty_message, later_timestamp)

# InputError: Cannot send empty messsages with 'whitespace'
def test_invalid_message_spaces(channel_with_user, get_current_time):
    sender = channel_with_user
    current_timestamp = get_current_time
    later_timestamp = current_timestamp + 3
    empty_message = "  "
    with pytest.raises(InputError):
        message_sendlater(sender['token'], sender['c_id'], empty_message, later_timestamp)

# InputError: Message is more than 1000 characters
def test_invalid_message_1001(channel_with_user, get_current_time):
    sender = channel_with_user
    current_timestamp = get_current_time
    later_timestamp = current_timestamp + 3

    invalid_message = "*" * 1001
    with pytest.raises(InputError):
        message_sendlater(sender['token'], sender['c_id'], invalid_message, later_timestamp)

# AccessError: The authorised user has not joined the channel that they are 
#              are trying to post to
def test_invalid_sender(channel_with_user, get_current_time):
    owner = channel_with_user
    current_timestamp = get_current_time
    later_timestamp = current_timestamp + 3
    # Seperate user who is not in the channel
    auth_register("invalid_sender@email.com", "password", "Firstname", "Lastname")
    invalid_sender = auth_login("invalid_sender@email.com", "password")
    
    with pytest.raises(AccessError):
        message_sendlater(invalid_sender['token'], owner['c_id'], "Test Message", later_timestamp)

# Input Error: The user is trying to send a time in the past
def test_invalid_time(channel_with_user, get_current_time):
    sender = channel_with_user
    current_timestamp = get_current_time
    # Set the time as a time in the past
    past_timestamp = current_timestamp - 3
    with pytest.raises(InputError):
        message_sendlater(sender['token'], sender['c_id'], "Test Message", past_timestamp)
