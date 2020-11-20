"""
channel.py

Main Modules:
    channel_invite: invites a user to a channel
    channel_details: returns a channel's details
    channel_messages: retrieves 50 messages from a channel
    channel_leave: makes a user leave a channel
"""

from data               import data
from error              import InputError, AccessError
from helper             import token_validator, u_id_validator, is_flockr_owner, channel_validator
from implement.auth     import auth_register, auth_login
from implement.channels import channels_create, channels_list, channels_listall

def channel_invite(token, channel_id, u_id):
    """
    channel_invite

    Args:
        token: authorises user
        channel_id: to specify the channel to invite user to
        u_id: to specify user to invite

    Returns:
        empty dictionary {} 

    Raises:
        AccessError when user is already in the channel
        AccessError when token is invalid
    """

    token_validator(token)
    u_id_validator(u_id)
    channel_validator(channel_id)

    # Verify that the channel_id is valid
    for channel in data['channels']:
        if channel_id == channel['channel_id']:
            if u_id in channel['all_members']:
                raise AccessError("User is already in the channel.")
            else: 
            # user is not in the channel and it is safe to invite and add the user
                channel['all_members'].append(u_id)

    return {
    }


def channel_details(token, channel_id):
    """
    channel_details

    Args:
        token: authorises user
        channel_id: to specify the channel to retrieve details from

    Returns:
        dictionary containing name, owner members and all members

    Raises:
        AccessError when user not a member of the channel
        AccessError when token is invalid
    """

    user_token = token_validator(token)
    user_token_id = user_token['u_id']
    channel_validator(channel_id)

    owner_members = []
    all_members = []
    for channels in data['channels']:
        if channel_id == channels['channel_id']:
            name = channels['name']
            owners = channels['owner_members']
            members = channels['all_members']

            # Check if user is authorised
            if user_token_id not in members:
                raise AccessError("Authorised user is not a member of the channel.")

            for user in owners:
                for userdata in data['users']:
                    if user == userdata['u_id']:
                        fname = userdata['name_first']
                        lname = userdata['name_last']
                        owner_list = {
                            'u_id': userdata['u_id'],
                            'name_first': fname,
                            'name_last': lname,
                            'profile_img_url': userdata['profile_img_url'],
                        }
                        owner_list_copy = owner_list.copy()
                        owner_members.append(owner_list_copy)

            for user in members:
                for userdata in data['users']:
                    if user == userdata['u_id']:
                        fname = userdata['name_first']
                        lname = userdata['name_last']
                        member_list = {
                            'u_id': userdata['u_id'],
                            'name_first': fname,
                            'name_last': lname,
                            'profile_img_url': userdata['profile_img_url'],
                        }
                        member_list_copy = member_list.copy()
                        all_members.append(member_list_copy)
    return {
        'name': name,
        'owner_members': owner_members,
        'all_members': all_members
    }

# Assumption: start is an int
def channel_messages(token, channel_id, start):
    """
    channel_messages

    Args:
        token: authorises user
        channel_id: to specify the channel to retrieve messages from
        start: from the most recent message to start retrieving 50 messages from newest to oldest

    Returns:
        a dictionary of message_details, starting message_id, ending message_id

    Raises:
        AccessError when user is not a member of given channel
        InputError when starting message_id is greater than total number of messages in channel
    """

    token_validator(token)
    channel_validator(channel_id)
    start_return = start

    channel_messages = {}

    all_channels = channels_listall(token) 
    for channel in all_channels['channels']:
        if channel_id == channel['channel_id']:
            channel_messages['messages'] = channel['messages']

    # If there are no messages in the channel 
    if not channel_messages['messages']:
        fetched_messages = []
        end = -1

        return {
        'messages': fetched_messages,
        'start': start_return,
        'end': end
    }

    # Check authorised user
    auth_not_in_channel = True
    users_channels = channels_list(token) 
    for channel in users_channels['channels']:
        if channel_id == channel['channel_id']:
            auth_not_in_channel = False

    if auth_not_in_channel:
        raise AccessError("Authorised user is not a member of channel.")

    # Check for start is within messages
    start_not_valid = True
    message_counter = 0
    for message in channel_messages['messages']:
        if message_counter == start:
            start_not_valid = False
        message_counter += 1

    if start_not_valid:
        raise InputError("Start is greater than the total number of messages in the channel.")

    # Fetch Channel Messages
    end = start + 50
    fetched_messages = []
    
    # Loops until message has reached the end or last message
    # To fetch message which corresponds to start which increments
    message_counter = 0
    messages_fetched_counter = 0
    for message in channel_messages['messages']:
        # If messages has fetched 50 messages
        if messages_fetched_counter == 50:
            break

        # Fetch messages when start matches with message
        if start == message_counter:
            fetched_messages.append(message)
            start += 1
            messages_fetched_counter += 1

        message_counter += 1

    # Check if no more messages to fetch
    if start != end:
        end = -1

    return {
        'messages': fetched_messages,
        'start': start_return,
        'end': end
    }


def channel_leave(token, channel_id):
    """
    channel_leave

    Args:
        token: authorises user
        channel_id: to specify the channel to leave

    Returns:
        empty dictionary {}

    Raises:
        AccessError when user not a member of the channel
        AccessError when token is invalid
    """

    user = token_validator(token)
    channel_validator(channel_id)

    # Removes the user
    for channel in data['channels']:
        if channel_id == channel['channel_id']:
            # Check if user is a member of channel
            if user['u_id'] in channel['all_members']:
                channel['all_members'].remove(user['u_id'])

                if user['u_id'] in channel['owner_members']:
                    channel['owner_members'].remove(user['u_id'])
            else:
                raise AccessError("Authorised user is not a member of the channel.")

    return {}

def channel_join(token, channel_id):
    """
    channel_join

    Args:
        token: authorises user
        channel_id: to specify the channel to join

    Returns:
        empty dictionary {}

    Raises:
        AccessError when user already part of channel channel
        AccessError when channel ID refers to a private channel that user 
        doesn't have permissions in.
        AccessError when token is invalid
    """

    user = token_validator(token)
    channel_validator(channel_id)
    channels = data['channels']

    # Locate the relevant channel in data
    for channel in channels:
        if channel_id == channel['channel_id']:

            # Check that the channel_id is public 
            if channel['is_public'] or is_flockr_owner(token, user['u_id']):
                if user['u_id'] not in channel['all_members']:
                # Now it is safe to add the user to the channel
                    channel['all_members'].append(user['u_id'])
                else:
                    raise AccessError("The user is already in the channel.")
            else:
                raise AccessError("Channel ID refers to a channel that is private.")

    return {}

def channel_addowner(token, channel_id, u_id):
    """
    channel_addowner

    Args:
        token: authorises user
        channel_id: to specify the channel to add owner to 
        u_id: to specify user to make owner

    Returns:
        empty dictionary {]}

    Raises:
        AccessError when user authorised user is not an owner of the flockr, 
        or an owner of specified channel
        InputError when user is already an owner to specified channel
        AccessError when token is invalid
    """

    preexisting_owner = token_validator(token)
    channel_validator(channel_id)
    u_id_validator(u_id)

    for channel in data['channels']:
        if channel_id == channel['channel_id']:

            # Checking if the owner is officially in owner_members
            if preexisting_owner['u_id'] in channel['owner_members'] or is_flockr_owner(token, preexisting_owner['u_id']):

                # Check if the potential owner is not already an owner
                if u_id not in channel['owner_members']:

                    # Now it is safe to add the user to the channel
                    channel['owner_members'].append(u_id)

                else: 
                    raise InputError("User is already an owner.")

            else: 
                raise AccessError("Authorised user is not an owner of the flockr, \
                                or an owner of this channel")
    
    return {}


def channel_removeowner(token, channel_id, u_id):
    """
    channel_removeowner

    Args:
        token: authorises user
        channel_id: to specify the channel to remove owner from
        u_id: to specify user to make owner

    Returns:
        empty dictionary {}

    Raises:
        AccessError when user authorised user is not an owner of the flockr, 
        or an owner of specified channel
        InputError when user is already an owner to specified channel
        AccessError when token is invalid
    """

    channel_remover = token_validator(token)
    u_id_validator(u_id)
    channel_departee = u_id
    channel_validator(channel_id)

    # Locate the relevant channel in data
    for channel in data['channels']:
        if channel_id == channel['channel_id']:
            # Verify that the 'remover' is an owner
            if channel_remover['u_id'] in channel['owner_members'] or is_flockr_owner(token, channel_remover['u_id']):

                # Verify that the 'departee' is an owner
                if channel_departee in channel['owner_members']:

                    # It is now safe to remove the 'channel_departee'
                    channel['owner_members'].remove(channel_departee)

                else:
                    raise InputError("The user that is being removed is not an owner.")

            else:
                raise AccessError("Authorised user is not an owner of the flockr, \
                                   or an owner of this channel")

    return {}
