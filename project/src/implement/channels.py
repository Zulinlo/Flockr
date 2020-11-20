"""
channels.py

Helper Modules:
    new_channel_id: creates a channel_id for a new channel

Main Modules:
    channels_list: gets all channels the user is in
    channels_listall: gets all channels
    channels_create: creates a new channel
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

from data           import data
from helper         import token_validator
from error          import InputError

def new_channel_id():
    if not len(data['channels']):
        channel_id = 0
    else:
        for channel in data['channels']:
            last_channel_id = channel['channel_id']

        channel_id = last_channel_id + 1
    return channel_id
    
def channels_list(token):
    """
    channels_list

    Args:
        token: authorises user

    Returns:
        a dictionary of all channels the user is in
    """

    user = token_validator(token)

    users_channels = []
    for channel in data['channels']:
        for users in channel['all_members']:
            if users == user['u_id']:
                users_channels.append(channel)

    return {
        'channels': users_channels
    }

def channels_listall(token):
    """
    channels_listall

    Args:
        token: authorises user

    Returns:
        a dictionary of all channels that exist and their information
    """

    token_validator(token)
    
    all_channels = []
    for channels in data['channels']:
        list_channel = channels
        list_channel_copy = list_channel.copy()
        all_channels.append(list_channel_copy)

    return {
        'channels': all_channels
    }

def channels_create(token, name, is_public):
    """
    channels_create

    Args:
        token: authorises user
        name: name for new channel
        is_public: determines if new channel will be public or private

    Returns:
        the channel_id of created channel

    Raises:
        InputError when channel length is not within 1 to 20 characters
        InputError when is_public is not equal to True or False
    """

    user = token_validator(token)

    # Check if name is valid
    name_valid = 1 <= len(name) <= 20
    if not name_valid:
        raise InputError("Channel name is not within 1 to 20 characters")

    # Check if is_public is a true or false boolean
    # For example: rejects is_public = 'djaspo' which would normally be True
    if is_public not in (True, False):
        raise InputError("Undefined channel privacy to be public or private")

    # Determine channel_id for this channel
    channel_id = new_channel_id()

    # Input created channel into data
    data['channels'].append(
        {
            'channel_id': channel_id,
            'name': name,
            'owner_members': [user['u_id']],
            'all_members': [user['u_id']],
            'is_public': is_public,
            'time_finish': None,
            'messages': []
        }
    )

    return {
        'channel_id': channel_id
    }
