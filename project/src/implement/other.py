"""
other.py

Main Modules:
    clear: resets the internal data of the application to its inititial state
    users_all: returns all users in the data
    search: Returns a collection of messages in all of the channels that the user has joined that match a given query
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

from data               import data
from helper             import token_validator, u_id_validator, is_flockr_owner
from implement.channels           import channels_list
from error              import AccessError, InputError
import re

def clear():
    '''
    Resets the internal data of the application to its initial state
    '''

    data['users'].clear()
    data['channels'].clear()
    data['message_counter'] = 0
    pass

def users_all(token):
    '''
    users_all

    Args:
        token: authorises user
    
    Returns:
        users: information about all users in the data
    
    Raises:
        AccessError when token is not valid
    '''    
    # Verify that token is valid
    token_validator(token)
    
    # Find and return all users in the data
    all_users = []
    for users in data['users']:
        user = {'u_id': users['u_id'], 
                'email': users['email'], 
                'name_first': users['name_first'],
                'name_last': users['name_last'],
                'handle_str': users['handle_str'],
                'profile_img_url': users['profile_img_url']
                }
        all_users.append(user)

    return {
        'users': all_users
    }


def admin_userpermission_change(token, u_id, permission_id):
    """
    admin_userpermission_change

    Helper Modules:
        user_validator: validates if user exists

    Args:
        token: authorises user
        u_id: the targeted user to change permission_id
        permission_id: can only be 1 (owner) and 2 (member)

    Returns:
        Empty dictionary but changes a user's permissions

    Raises:
        InputError when u_id does not refer to a valid user within the channel
        InputError when permission_id is not valid (1 or 2)
        AccessError when the authorised user (token) is not an owner
    """

    # Check if the token is valid
    user = token_validator(token)

    # Check if the u_id is valid
    u_id_validator(u_id)

    # Checks if permission_id is valid
    if permission_id not in (1, 2):
        raise InputError("Permission value has to be 1 or 2")

    # Checks if authorised user is a Flockr owner
    if not is_flockr_owner(token, user['u_id']):
        raise AccessError("The authorised user is not a Flockr owner")

    # Change target u_id's permission_id
    for user in data['users']:
        if user['u_id'] == u_id:
            user['permission_id'] = permission_id

def search(token, query_str):
    '''
    Given a query string, return a collection of messages in all of 
    the channels that the user has joined that match the query

    Search Method: locates substrings inside messages using regex function search()
    '''
    owner = token_validator(token)

    if query_str == "" or query_str.isspace():
        raise InputError("Query string is empty or contains whitespace")

    # Assumption: Uppercase and lowercase letters are treated as the same
    query_str = query_str.lower()

    user_messages = []

    for channel in data['channels']:
        # Verify that the user is part of a channel
        if owner['u_id'] in channel['all_members']:
                # Loop through all messages in the channel
                for current in channel['messages']:
                    if re.search(query_str, current['message'].lower()):         
                        current_message = {
                            'message_id': current['message_id'],
                            'u_id': current['u_id'],
                            'message': current['message'],
                            'time_created': current['time_created'],
                            'reacts': [
                                {
                                    'react_id': 0,
                                    'u_ids': [],
                                    'is_this_user_reacted': False,
                                }
                            ],
                            'is_pinned': current['is_pinned'],
                        }                
                        user_messages.append(current_message)
        else:
            raise AccessError("The user is not part of any channels")

    if user_messages == []:
        raise InputError("There were no messages found")

    return {'messages': user_messages}
