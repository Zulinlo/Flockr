'''
message_remove_test.py

Fixtures:
    channel_with_user: registers and logs in a user, and then creates a public channel

Test Modules:
    test_owner_message_remove_success: success case for when owner removes their own message
    test_sender_message_remove_success: success case for when sender removes their own message    
    test_owner_removes_sender_message_success: success case for when owner removes a sender's message
    test_multiple_messages_success: success case for when multiple messages sent but one removed
    test_invalid_message_id: fail case for invalid message_id
    test_reused_message_id: fail case for reused message_id
    test_unauthorised_remover: fail case due to unauthorised remover 
'''
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import pytest
from implement.message        import message_send, message_remove
from error          import AccessError, InputError
from implement.other          import clear
from implement.auth           import auth_register, auth_login
from implement.channels       import channels_create
from implement.channel        import channel_join, channel_messages
from datetime       import datetime, timezone

# Arguments: token, message_id
# Constraints:
# - Message has to exist
# - Message being removed must be removed by the user who sent it
# - AND/OR the user requesting the remove is an owner of the channel/flockr

# Assumption: message_id is not affected by other messages being removed 

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

'''Success Cases:'''
# Owner of the channel removes their own message
def test_owner_message_remove_success(channel_with_user):
    owner = channel_with_user

    # Ensure there's no messages in the channel to begin with
    messages = channel_messages(owner['token'], owner['c_id'], 0)['messages']
    assert not messages

    # Send message 
    message_id = message_send(owner['token'], owner['c_id'], "Test Message 1")

    # Verify the message was sent inbetween creating and removing
    message = channel_messages(owner['token'], owner['c_id'], 0)['messages']
    
    assert message[0]['message_id'] == 0
    assert message[0]['u_id'] == 0
    assert message[0]['message'] == 'Test Message 1'

    # Remove message
    message_remove(owner['token'], message_id['message_id'])

    # Verify that the message was removed
    messages = channel_messages(owner['token'], owner['c_id'], 0)['messages']
    assert not messages

#Pass case for when the sender of a message removes it
def test_sender_message_remove_success(channel_with_user, ):  
    owner = channel_with_user

    # Create second user who will send the message
    auth_register("user@email.com", "password", "First", "Last")
    sender = auth_login("user@email.com", "password")
    channel_join(sender['token'], owner['c_id'])

    # Ensure there's no messages in the channel to begin with
    messages = channel_messages(owner['token'], owner['c_id'], 0)['messages']
    assert not messages

    # Send the message with a user other than the owner
    message_id = message_send(sender['token'], owner['c_id'], "Test Message")

    # Verify the message was sent inbetween creating and removing
    message = channel_messages(owner['token'], owner['c_id'], 0)['messages']
    
    assert message[0]['message_id'] == 0
    assert message[0]['u_id'] == 1
    assert message[0]['message'] == 'Test Message'

    # Remove message
    message_remove(sender['token'], message_id['message_id'])

    # Verify that the message was removed
    messages = channel_messages(owner['token'], owner['c_id'], 0)['messages']
    assert not messages


# Sender sends a message and then Owner removes it
def test_message_remove_sender_success(channel_with_user):
    owner = channel_with_user

    # Create second user who will send the message
    auth_register("user@email.com", "password", "First", "Last")
    sender = auth_login("user@email.com", "password")
    channel_join(sender['token'], owner['c_id'])

    # Ensure there's no messages in the channel to begin with
    messages = channel_messages(owner['token'], owner['c_id'], 0)['messages']
    assert not messages

    # Send the message with a user other than the owner
    message_id = message_send(sender['token'], owner['c_id'], "Test Message")

    # Verify the message was sent inbetween creating and removing
    message = channel_messages(owner['token'], owner['c_id'], 0)['messages']
    # assert message == [
    #     {'message_id': 0, 'u_id': 1, 'message': 'Test Message', 'time_created': timestamp}
    # ]
    assert message[0]['message_id'] == 0
    assert message[0]['u_id'] == 1
    assert message[0]['message'] == 'Test Message'

    # Remove message
    message_remove(owner['token'], message_id['message_id'])

    # Verify that the message was removed
    messages = channel_messages(owner['token'], owner['c_id'], 0)['messages']
    assert not messages

# Multiple messages sent but only 1 message removed
def test_multiple_messages_success(channel_with_user):
    owner = channel_with_user

    # Ensure there's no messages in the channel to begin with
    messages = channel_messages(owner['token'], owner['c_id'], 0)['messages']
    assert not messages

    # Assumption: No need to test whether a message has been sent with message_send as this would be covered by message_send functions
    # Send 2 messages
    message_to_remove = message_send(owner['token'], owner['c_id'], "Test Message 1")
    message_send(owner['token'], owner['c_id'], "Test Message 2")

    # Verify the message was sent inbetween creating and removing
    message = channel_messages(owner['token'], owner['c_id'], 0)['messages']

    assert message[0]['message_id'] == 0
    assert message[0]['u_id'] == 0
    assert message[0]['message'] == 'Test Message 1'

    assert message[1]['message_id'] == 1
    assert message[1]['u_id'] == 0
    assert message[1]['message'] == 'Test Message 2'

    # Remove 1st message
    message_remove(owner['token'], message_to_remove['message_id'])

    # Verify that the 2nd message has become the first message in the channel
    message = channel_messages(owner['token'], owner['c_id'], 0)['messages']

    assert message[0]['message_id'] == 1
    assert message[0]['u_id'] == 0
    assert message[0]['message'] == 'Test Message 2'

'''Error Cases:'''
# Fail case due to invalid message_id
def test_invalid_message_id(channel_with_user):
    owner = channel_with_user

    message_send(owner['token'], owner['c_id'], "Test Message 1")

    invalid_message_id = -1
    with pytest.raises(InputError):
        message_remove(owner['token'], invalid_message_id)

# Fail case due to remove being called twice with same message_id (message no longer exists the second time)
def test_reused_message_id(channel_with_user):
    owner = channel_with_user

    # Ensure there's no messages in the channel to begin with
    messages = channel_messages(owner['token'], owner['c_id'], 0)['messages']
    assert not messages

    # Send message
    message_id = message_send(owner['token'], owner['c_id'], "Test Message 1")
    message_remove(owner['token'], message_id['message_id'])

    # Failed message removal due to message already having been removed
    with pytest.raises(InputError):
        message_remove(owner['token'], message_id['message_id'])


def test_unauthorised_remover(channel_with_user):
    owner = channel_with_user

    # Ensure there's no messages in the channel to begin with
    messages = channel_messages(owner['token'], owner['c_id'], 0)['messages']
    assert not messages

    # Send the first message
    message_id = message_send(owner['token'], owner['c_id'], "Test Message 1")

    # Register a second user
    auth_register("unauthorised@gmail.com", "password1", "unauthorised", "remover")
    unauthorised_remover = auth_login("unauthorised@gmail.com", "password1")
    channel_join(unauthorised_remover['token'], owner['c_id'])

    # Access Error, as the user trying to remove the message did not send it and is not an owner
    with pytest.raises(AccessError):
        message_remove(unauthorised_remover['token'], message_id['message_id'])

def test_flockr_owner_remover(channel_with_user):
    clear()
    # Creating the flockr owner
    auth_register("flockr_owner@email.com", "flockr_ownerpassword", "flockr_ownerFirstname", "flockr_ownerLastname")
    flockr_owner = auth_login("flockr_owner@email.com", "flockr_ownerpassword")
    
    # Creating the owner and their own channel
    auth_register("owner@email.com", "ownerpassword", "ownerFirstname", "ownerLastname")
    owner = auth_login("owner@email.com", "ownerpassword")
    public = True
    channel_id = channels_create(owner['token'], "Channel", public)

    # Creating the message via the owner
    message_id = message_send(owner['token'], channel_id['channel_id'], "Test Message 1")
    message = channel_messages(owner['token'], channel_id['channel_id'], 0)['messages']
    # assert message == [
    #     {'message_id': 0, 'u_id': 1, 'message': 'Test Message 1', 'time_created': timestamp}
    # ]
    assert message[0]['message_id'] == 0
    assert message[0]['u_id'] == 1
    assert message[0]['message'] == 'Test Message 1'

    # Removing the message via the flockr owner
    message_remove(flockr_owner['token'], message_id['message_id'])
    messages = channel_messages(owner['token'], channel_id['channel_id'], 0)['messages']
    assert not messages
