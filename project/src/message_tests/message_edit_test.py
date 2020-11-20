'''
message_edit_test.py

Fixtures:
    register_login: registers a new user and logs that user in
    create_channel: creates a public channel

Test Modules:
    test_unauthorised_user_message: fail case where the user editing the message is not a creator of the message or an owner of the channel/flockr
    test_invalid_message_id: fail case where message id is not valid (i.e. the message doesn't exist)
    test_member_edits_own_message: success case where the user editing their message sent the message
    test_owner_edits_user_message: success case owner edits a message in the channel
    test_empty_message: success case where new message request is empty, deleting the message
    test_multiple_edits: success case for when edits are made to multiple messages
'''
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import pytest
from error          import InputError, AccessError
from implement.other          import clear
from implement.auth           import auth_register, auth_login
from implement.channels       import channels_create
from implement.channel        import channel_join, channel_details, channel_messages
from implement.message        import message_send, message_edit

# Clarification of Variable Names:
# - owner_c_id = Owner's Channel ID
# - owner_m_id = Owner's Message ID

@pytest.fixture
def register_login():
    clear()
    auth_register("user@email.com", "password", "Richard", "Shen")
    user = auth_login("user@email.com", "password")
    return {
        "u_id": user["u_id"],
        "token": user["token"]
    }

@pytest.fixture
def create_channel(register_login):
    # register a user and log them in so they have a token.
    token = register_login
    public = True
    c_id = channels_create(token["token"], "Channel", public)
    return {
        'c_id': c_id['channel_id']
    }

'''Fail Cases'''
# Scenario: User who is editing the message is not the creator of the message
#           and also isn't the owner of the channel
def test_unauthorised_user_message(register_login, create_channel):
    owner = register_login
    owner_c_id = create_channel['c_id']
    owner_m_id = message_send(owner['token'], owner_c_id, "New Message")['message_id']

    # creating a new user who isnt the owner of the channel, and did not create a message
    auth_register("test2@gmail.com", "password2", "Richard2", "Shen2")
    user_2 = auth_login("test2@gmail.com", "password2")
    channel_join(user_2['token'], owner_c_id)

    # should raise an AccessError since the new user is not an owner of the channel and didn't create the message
    with pytest.raises(AccessError):
        message_edit(user_2['token'], owner_m_id, "Edited Message")

# Testing if the message_id is valid or not
def test_invalid_message_id(register_login, create_channel):
    owner = register_login
    owner_c_id = create_channel['c_id']
    message_send(owner['token'], owner_c_id, "New Message")

    invalid_message_id = -1
    with pytest.raises(AccessError):
        message_edit(owner['token'], invalid_message_id, "Edit Message")

'''Success Cases'''
# Scenario: The user requesting the edit is not an owner but sent the message
#           originally, therefore has permission to edit.
def test_member_edits_own_message(register_login, create_channel):
    owner = register_login
    owner_c_id = create_channel['c_id']
  
    # Creating a new user who is not the owner, and joins the channel as a member
    auth_register("test2@gmail.com", "password2", "Richard2", "Shen2")
    user_2 = auth_login("test2@gmail.com", "password2")
    channel_join(user_2['token'], owner_c_id)

    # Verify the new user is not an owner
    channel = channel_details(owner['token'], owner_c_id)
    assert user_2['u_id'] not in channel['owner_members']

    # User 2's message id
    user_2_m_id = message_send(user_2['token'], owner_c_id, "Member's Message")['message_id']

    # Ensure that it is user 2's message
    messages = channel_messages(user_2['token'], owner_c_id, 0)['messages']
    assert user_2['u_id'] == messages[0]['u_id']

    # User 2 edits the message
    new_message = "user_2 can edit their own message"
    message_edit(user_2['token'], user_2_m_id, new_message)

    # Ensure the message is edited
    messages = channel_messages(user_2['token'], owner_c_id, 0)['messages']
    assert new_message == messages[0]['message']

# Scenario: Owner is able to edit any message in the channel
def test_owner_edits_user_message(register_login, create_channel):
    owner = register_login
    owner_c_id = create_channel['c_id']
   
   # Create a new user who is not the owner, and joins the channel as a member
    auth_register("test2@gmail.com", "password2", "Richard2", "Shen2")
    user_2 = auth_login("test2@gmail.com", "password2")
    channel_join(user_2['token'], owner_c_id)

    user_2_m_id = message_send(user_2['token'], owner_c_id, "User 2's Message")['message_id']

    # Ensure that the owner can edit user 2's message
    owner_message = "Owner has authority to edit"
    message_edit(owner['token'], user_2_m_id, owner_message)

    message = channel_messages(owner['token'], owner_c_id, 0)
    assert owner_message == message['messages'][0]['message']

# Scenario: New message requested is empty, delete the original message entirely
def test_empty_message(register_login, create_channel):
    owner = register_login
    owner_c_id = create_channel['c_id']

    # Create 3 messages
    message_send(owner['token'], owner_c_id, "Message 1")['message_id']
    owner_m_id = message_send(owner['token'], owner_c_id, "Message 2")['message_id']
    message_send(owner['token'], owner_c_id, "Message 3")['message_id']

    all_messages = channel_messages(owner['token'], owner_c_id, 0)['messages']
    message_1 = channel_messages(owner['token'], owner_c_id, 0)['messages'][0]
    message_3 = channel_messages(owner['token'], owner_c_id, 0)['messages'][2]
 
    # Deletes the 2nd message
    empty_message = ""
    assert len(all_messages) == 3
    message_edit(owner["token"], owner_m_id, empty_message)

    # Ensure that the right message was removed
    all_messages = channel_messages(owner['token'], owner_c_id, 0)['messages']
    assert len(all_messages) == 2

    assert all_messages == [message_1, message_3]

# If the message edit is successful, the original message should now equal to the new message
def test_multiple_edits(register_login, create_channel):
    owner = register_login
    owner_c_id = create_channel['c_id']

    # 3 messages are created, the 2nd and 3rd will be edited
    message_send(owner['token'], owner_c_id, "Message 1")['message_id']
    edit_request_1 = message_send(owner['token'], owner_c_id, "Message 2")['message_id']
    edit_request_2 = message_send(owner['token'], owner_c_id, "Message 3")['message_id']

    # Edit the 2nd message
    edited_message = "Edited Message 2"
    message_edit(owner["token"], edit_request_1, edited_message)

    # Check the 2nd message was editied correctly
    updated_message = channel_messages(owner['token'], owner_c_id, 0)['messages'][1]['message']
    assert edited_message == updated_message

    # Edit the 3rd Message
    edited_message = "Edited Message 3"
    message_edit(owner["token"], edit_request_2, edited_message)

    # Check the 3rd message was editied correctly
    updated_message = channel_messages(owner['token'], owner_c_id, 0)['messages'][2]['message']
    assert edited_message == updated_message

def test_flockr_owner_permissions(register_login, create_channel):
    flockr_owner = register_login

    # Creates a new user who is the owner of a channel
    auth_register("test2@gmail.com", "password2", "Richard2", "Shen2")
    user_2 = auth_login("test2@gmail.com", "password2")

    c_id = channels_create(user_2["token"], "Channel", True)['channel_id']

    # Create a new user who is not flockr owner, and is a member of a channel,
    # sends a message
    auth_register("test3@gmail.com", "password3", "Richard3", "Shen3")
    user_3 = auth_login("test3@gmail.com", "password3")
    channel_join(user_3['token'], c_id)
    channel_join(flockr_owner['token'], c_id)

    m_id = message_send(user_3['token'], c_id, "First Message")['message_id']

    message_edit(flockr_owner['token'], m_id, "Edited Message")

    # Check the message was edited correctly
    updated_message = channel_messages(flockr_owner['token'], c_id, 0)['messages'][0]['message']

    assert updated_message == "Edited Message"
