"""
standup.py

Helper Modules:
    get_time: gets the current time in the form of a UNIX timestamp, unless parameter is an int then calculate timestamp
    thread_standup: function which threads, when time finishes it sends message

Main Modules:
    standup_start: initates a standup period where standup sending will buffer messages and send them all to the message queue from the user who initiated the standup_start
    standup_active: for a given channel, returns whether a standup is active currently and when it will end
    standup_send: sends a message to the standup to buffer
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

from data               import data
from helper             import channel_validator, token_validator
from implement.message            import message_send
from error              import AccessError, InputError
from datetime           import datetime, timezone
import threading, time

from implement.channel  import channel_details
from implement.user               import user_profile

def get_timestamp(length = 0):
    # Get current time
    current_time = datetime.utcnow()

    # Calculate UNIX timestamp + the length arg (seconds)
    timestamp = int(current_time.replace(tzinfo=timezone.utc).timestamp()) + length

    return timestamp

class Standup:
    def __init__(self):
        self.standup_queue = []
        # standup_queue example:
        # standup_queue = [
        #   'handle_str': 'John',
        #   'message': 'Example Message',
        # ]
    
    # for standup_send
    def add_standup_queue(self, message, handle_str):
        add_message = {
            'handle_str': handle_str,
            'message': message,
        }
        self.standup_queue.append(add_message)
        pass

    def reset_standup_queue(self):
        self.standup_queue = []

    # def remove_standup_queue(self, message_id):
        # pass        # bonus function?

    def get_packed_message(self):
        # To pack all messages sent within the standup
        packed_message = ''
        messages = self.standup_queue
        for message in messages:
            packed_message += message['handle_str'] + ': ' + message['message'] + '\n'
        packed_message = packed_message.rstrip('\n')

        if packed_message == '':
            return False

        return packed_message

# Create standup class
standup = Standup()

def thread_standup(token, channel_id, length):
    # Creates a class which will buffer all messages
    standup.reset_standup_queue()

    # Pauses this thread until standup finishes executing
    time.sleep(length)

    # When standup time finishes, send all standup messages into a message
    packed_message = standup.get_packed_message()

    # Get target channel
    channel = None
    for channels in data['channels']:
        if channels['channel_id'] == channel_id:
            channel = channels

    # If standup is empty then don't send a standup message
    if not packed_message:
        # time_finish is reset after the channel standup is done
        channel['time_finish'] = None

        return
    
    # message_send is not used as the check for the message length needs to be ignored
    # since the packed message contains 'unecessary characters' such as the handle_str
    sender = token_validator(token)
    message_id = data['message_counter']

    # time_finish is reset after the channel standup is done
    channel['time_finish'] = None

    # Append standup message into the data
    data['message_counter'] += 1
    channel['messages'].append({
        'message_id': message_id, 
        'u_id': sender['u_id'], 
        'message': packed_message, 
        'time_created': get_timestamp(),
        'reacts': [
            {
                'react_id': 0,
                'u_ids': [],
                'is_this_user_reacted': False
            }
        ],
        'is_pinned': False,
    })

    return {
        'message_id': message_id,
    }

def standup_start(token, channel_id, length):
    """
    standup_start

    Args:
        token: authorises user
        channel_id: the target channel to initiate the standup in
        length: how long the standup will last (in seconds)

    Returns:
        time_finish: the time the startup will end and consequently send the start up messages into the message queue of the channel
    """
    token_validator(token)
    channel_validator(channel_id)  

    # Check if there is a standup currently running in the channel
    if standup_active(token, channel_id)['is_active']:
        raise InputError("There is already a standup currently active")

    # Start the standup period, for length (seconds) where messages using standup 
    # will be sent to a standup_queue, then all added to the channel_messages by a 
    # packed message sent by the creator of the standup when the standup finishes
    time_finish = get_timestamp(length)
    standup_start = threading.Thread(target=thread_standup, args=(token, channel_id, length))
    standup_start.start()

    for channel in data['channels']:
        if channel['channel_id'] == channel_id:
            channel['time_finish'] = time_finish
    
    return {
        'time_finish': time_finish
    }

def standup_active(token, channel_id):
    """
    standup_active

    Args:
        token: authorises user
        channel_id: the target channel to get startup details from

    Returns:
        is_active: if there is currently an active standup True, otherwise False
        time_finish: the time the startup will end, or None if no active standup
    """
    token_validator(token)
    channel_validator(channel_id)  

    time_finish = None
    for channel in data['channels']:
        if channel['channel_id'] == channel_id:
            time_finish = channel['time_finish']

    # There is currently a standup running in the channel
    if time_finish != None:
        return {
            'is_active': True,
            'time_finish': time_finish
        }
    # There is not currently a standup running in the channel
    else:
        return {
            'is_active': False,
            'time_finish': None
        }

def standup_send(token, channel_id, message):
    """
    standup_send
    
    Args:
        token: authorises user
        channel_id: the target channel to buffer a message to the active standup
        message: the message to buffer into the active standup
    """
    print(token)
    print(channel_id)
    print(message)

    u_id = token_validator(token)['u_id']
    channel_validator(channel_id)
    
    # Verify that the standup is currently active
    if not standup_active(token, channel_id)['is_active']:
        raise InputError("There is already a standup currently active")
    
    # Verify that the is under 1000 characters
    if len(message) > 1000:
        raise InputError("Message is more than 1000 characters")
    
    # Verifies that the user is a member of the channel
    channel_details(token, channel_id)

    handle_str = user_profile(token, u_id)['user']['handle_str']
    standup.add_standup_queue(message, handle_str)

    return {}
