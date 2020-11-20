"""
message.py

Main Modules:
    message_send: an authorised user sends a message to a channel
    message_remove: either channel/flockr owner or the message sender removes a message
    message_edit: either channel/flockr owner or the message sender edits a message
    message_pin: owner pins a specific message in a channel they are a member of
    message_unpin: owner unpins a pinned message in a channel
    message_react: user reacts a specific message in a channel they are a member of
    message_unreact: user removes a react they have placed on a specific message

Helper Modules:
    queue_message: appends a message to the channel at a later time with a prepared message_id

"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import threading
from data               import data
from error              import AccessError, InputError
from helper             import token_validator, channel_validator, is_flockr_owner
from datetime           import datetime, timezone

def message_send(token, channel_id, message):
    '''
    Send a message from authorised_user to the channel specified by channel_id
    '''
    sender = token_validator(token)
    channel_validator(channel_id)

    # Verify that the is under 1000 characters
    if len(message) > 1000:
        raise InputError("Message is more than 1000 characters")
    # Verify that the message is not empty or contains just whitespace
    elif message == "" or message.isspace():
        raise InputError("Message is empty or contains only whitespace")

    # Verify that the sender (token) is in the right channel
    message_id = data['message_counter']
    for channel in data['channels']:
        if channel_id == channel['channel_id']:
            current_time = datetime.utcnow()
            timestamp = int(current_time.replace(tzinfo=timezone.utc).timestamp())

            if sender['u_id'] in channel['all_members']:
                # Append message information into the data
                data['message_counter'] += 1
                channel['messages'].append({
                    'message_id': message_id, 
                    'u_id': sender['u_id'], 
                    'message': message, 
                    'time_created': timestamp,
                    'reacts': [
                        {
                            'react_id': 0,
                            'u_ids': [],
                            'is_this_user_reacted': False
                        }
                    ],
                    'is_pinned': False,
                })
            else:
                raise AccessError("The authorised user has not joined the channel \
                                   that they are are trying to post to.")
    return {
        'message_id': message_id,
    }

def message_remove(token, message_id):
    '''
    Either an authorised user (i.e. channel owner) or the sender of a message removes a message. Specified by message_id
    '''
    # Verify that the remover has a valid token
    remover = token_validator(token)

    # Locate the relevant message by looping through the channels and messages
    for channel in data['channels']:
        # Find the message to be removed
        for message_find in channel['messages']:
            if message_find['message_id'] == message_id:
                # If message has been found, check authorisation to remove
                # Remover is authorised if they are either the sender of the message or they are the owner of the channel
                if remover['u_id'] == message_find['u_id'] or remover['u_id'] in channel['owner_members'] or is_flockr_owner(token, remover['u_id']):
                    del channel['messages'][message_id]
                    return {}
                else:
                    raise AccessError("Sorry, you are neither the owner of the channel or creator of the message")
    
    # If the message was not found, raise Input Error
    raise InputError("The message you are trying to remove was not found")
    
# Assumption : The original message is asssumed to be valid since 
#              message_send() has to run prior to this function
# Assumption: When the user edits the message, the timestamp is not updated.
def message_edit(token, message_id, message):
    # Validate the authorised user
    editor = token_validator(token)
    new_message = message

    # Locate the message to edit by looping through channels then messages
    # If we fix channel_messages and call it, we won't have to loop through.
    message_found = False
    for channel in data["channels"]:
        for curr_message in channel["messages"]:
            # Find the message the user wants to edit
            if curr_message['message_id'] == message_id:
                # Check if user is flockr owner
                # Verify that the user is authorised to edit
                if editor['u_id'] == curr_message['u_id'] or editor["u_id"] in channel["owner_members"] or is_flockr_owner(token, editor["u_id"]):
                    # Safe to edit the message
                    message_found = True
                    break
                else: 
                    raise AccessError("Sorry, you are neither the owner of the channel or \
                                       creator of the message, you cannot edit the message")

    if message_found:
        if len(new_message) == 0:
            # The entire message including its details is deleted
            del channel['messages'][message_id]
        else:
            # The message in data is replaced with the new message
            curr_message['message'] = new_message
    else:
        raise AccessError("The message_id does not match the message you are trying to edit.")

    return {}

def message_pin(token, message_id):
    # pinner = the user who is requesting the message to be pinned
    pinner = token_validator(token)['u_id']

    # Locate the given message_id and verify it
    valid_message = False
    for channel in data['channels']:
        for message in channel['messages']:
            if message_id == message['message_id']:
                valid_message = True
                break

    if valid_message:
        if not message['is_pinned']:
            if pinner in channel['all_members'] or is_flockr_owner(token, pinner):
                if pinner in channel['owner_members'] or is_flockr_owner(token, pinner):
                    message['is_pinned'] = True
                else:
                    raise AccessError("Authorised user is not an owner")
            else:
                raise AccessError("Authorised user is not a member of the channel \
                                   that the message is within")
        else:
            raise InputError("Message with ID message_id is already pinned")
    else:
        raise InputError("message_id is not a valid message")

    return {}

def message_unpin(token, message_id):
    # pinner = the user who is requesting the message to be pinned
    unpinner = token_validator(token)['u_id']

    # Locate the given message_id and verify it
    valid_message = False
    for channel in data['channels']:
        for message in channel['messages']:
            if message_id == message['message_id']:
                valid_message = True
                break

    if valid_message:
        if message['is_pinned']:
            if unpinner in channel['all_members'] or is_flockr_owner(token, unpinner):
                if unpinner in channel['owner_members'] or is_flockr_owner(token, unpinner):
                    message['is_pinned'] = False
                else:
                    raise AccessError("Authorised user is not an owner")
            else:
                raise AccessError("Authorised user is not a member of the channel \
                                   that the message is within")
        else:
            raise InputError("Message with ID message_id is already unpinned")
    else:
        raise InputError("message_id is not a valid message")

    return {}

def message_react(token, message_id, react_id):
    user = token_validator(token)

    # Locate the message to edit by looping through channels then messages
    # If we fix channel_messages and call it, we won't have to loop through
    valid_message_id = False
    for channel in data['channels']:
        # Check if the user who is reacting to the message in the channel, is actually in the channel
        for current_message in channel['messages']:
            if current_message['message_id'] == message_id:
                valid_message_id = True
                break

    if user['u_id'] not in channel['all_members']:
        raise InputError("The user is not part of the channel, hence, has no permissions")

    if react_id not in (0, 1):
        raise InputError('The react_id for this message is invalid')            

    if valid_message_id:
        for react in current_message['reacts']:
            if user['u_id'] not in react['u_ids']:
                # React to the message by calling react_id == 1
                react_id = 1
                react['react_id'] = react_id
                react['u_ids'].append(user['u_id'])
                react['is_this_user_reacted'] = True
            else:
                raise InputError("The message with ID message_id already has an active react_id by the same user with ID u_id")
    else:
        raise InputError("The message_id does not match the message you are trying to react to")

    return {}


def message_unreact(token, message_id, react_id):
    user = token_validator(token)

    # Check is message exists
    valid_message_id = False
    for channel in data['channels']:
        # Check if the user who is reacting to the message in the channel, is actually in the channel
        for current_message in channel['messages']:
            if current_message['message_id'] == message_id:
                valid_message_id = True
                break

    if user['u_id'] not in channel['all_members']:
        raise InputError("The user is not part of the channel")

    if react_id != 1:
        raise InputError('The react_id for this message is invalid')       

    if valid_message_id:
        for react in current_message['reacts']:
            if user['u_id'] in react['u_ids']:
                react['u_ids'].remove(user['u_id'])
                react['is_this_user_reacted'] = False
            else:
                raise InputError("You have not reacted this message yet")
    else:
        raise InputError("The message you are trying to unreact was not found")

    return {}

def message_sendlater(token, channel_id, message, time_sent):
    '''
    message_sendlater

    Args:
        token: authorises user
        channel_id: the target channel for the message
        message: content of the message
        time_sent: the time at which the message will be sent into the channel
    
    Returns: 
        returns {message_id}

    Raises: 
        InputError when message is more than 1000 characters
        InputError when message is empty
        InputError when channel_id is not a valid channel
        InputError when the time sent is a time in the past
        AccessError when token is not valid
        AccessError when the user has not joined the channel they are trying to post to
    '''
    # Verify that the sender and channels are valid
    sender_u_id = token_validator(token)['u_id']
    channel_validator(channel_id)

    # Find the current time
    current_time = datetime.utcnow()
    current_timestamp = int(current_time.replace(tzinfo=timezone.utc).timestamp())

    # Verify that the is under 1000 characters
    if len(message) > 1000:
        raise InputError("Message is more than 1000 characters")
    # Verify that the message is not empty or contains just whitespace
    if message == "" or message.isspace():
        raise InputError("Message is empty or contains only whitespace")
    # Verify that the input time is not in the past
    if time_sent < current_timestamp:
        raise InputError("Scheduled time is in the past")
    # Verify that the user is in the channel
    for channel in data['channels']:
        if channel_id == channel['channel_id']:
            if sender_u_id not in channel['all_members']:
                raise AccessError("The authorised user has not joined the channel \
                                   that they are are trying to post to.")

    # Assign the message_id to be used for the queued up message
    message_id = data['message_counter']

    # Determine waiting time for the message to be sent
    waiting_time = int(time_sent - current_timestamp)

    # Start the timer to send the message
    delay_message = threading.Timer(waiting_time, queue_message, [sender_u_id, channel_id, message_id, message, time_sent])

    delay_message.start()

    # Update the message counter for other messages which may be sent
    data['message_counter'] += 1
    return {
        'message_id': message_id
    }

def queue_message(sender_u_id, channel_id, message_id, message, time_sent):
    '''
    queue_message

    Args:
        sender: identifies message sender
        channel_id: the target channel for the message
        message: content of the message
        time_sent: the time at which the message will be sent into the channel   
    '''  
    for channel in data['channels']:
        if channel_id == channel['channel_id']:
            channel['messages'].append({
                'message_id': message_id, 
                'u_id': sender_u_id, 
                'message': message, 
                'time_created': time_sent,
                'reacts': [
                    {
                        'react_id': 0,
                        'u_ids': [],
                        'is_this_user_reacted': False
                    }
                ],
                'is_pinned': False,
            })