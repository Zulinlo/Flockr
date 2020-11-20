"""
user.py

Main Modules:
    user_profile: returns nformation about a valid user.
    user_profile_setname: Updates an authorised user's first and last name.
    user_profile_setemail: Updates an authorised user's email address.
    user_profile_sethandle: Updates an authorised user's handle.
    user_profile_uploadphoto: Uploads an authorised user's profile picture.
    user_profile_getphoto: Retrieves target photo from url
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import re 
import os
import imgspy
import requests
import urllib.request
from PIL            import Image
import uuid 

from data           import data
from error          import InputError
from helper         import token_validator, u_id_validator

IMG_LOCATION = f"{os.getcwd()}/src/profile_pictures"

def user_profile(token, u_id):
    '''
    user_profile

    Args:
        token: authorises user
        u_id: identifies user in the flockr
    
    Returns:
        user: information about the user

    Raises:
        InputError when user_id does not refer to a valid user
        AccessError when token is not valid
    '''
    # Validates u_id and token
    u_id_validator(u_id)
    token_validator(token)

    user = {}
    # Finds the corresponding user based of u_id
    for users in data['users']:
        if u_id == users['u_id']:
            user = users

    return {
        'user': {
                'u_id': user['u_id'],
                'email': user['email'],
                'name_first': user['name_first'],
                'name_last': user['name_last'],
                'handle_str': user['handle_str'],
                'permission_id': user['permission_id'],
                'profile_img_url': user['profile_img_url'],
        },
    }

def user_profile_setname(token, name_first, name_last):
    """
        user_profile_setname

        Args:
            token: authorises user
            name_first: new first name for user
            name_last: new last name for user

        Returns:
            empty dictionary but changes user's name

        Raises:
            InputError when name_first is not within 1 to 50 characters inclusive
            InputError when name_last is not within 1 to 50 characters inclusive
            AccessError when token is not valid
    """

    # Validating the token
    user = token_validator(token)

    valid_first_name = 1 <= len(name_first) <= 50
    if not valid_first_name:
        raise InputError("Invalid first name length")
    
    valid_last_name = 1 <= len(name_last) <= 50
    if not valid_last_name:
        raise InputError("Invalid last name length")

    for users in data['users']:
        if users['u_id'] == user['u_id']:
            users['name_first'] = name_first
            users['name_last'] = name_last

    return {}

def user_profile_setemail(token, email):
    '''
    user_profile_setemail

    Args:
        token: authorises user
        email: the new email address
    
    Returns: 
        returns {}

    Raises:
        InputError when email is not valid
        InputError when email is already being used
        AccessError when token is not valid
    '''
    # Validating the token of the user
    user = token_validator(token)

    # Check that the new email is valid using the method provided
    regex = r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
    if (re.search(regex,email)):
        for users in data['users']:
            if users['email'] == email:
                raise InputError("The new email you are updating is currently being used")
    else: 
        raise InputError("The new email you are updating to is invalid")

    for users in data['users']:
        if users['u_id'] == user['u_id']:
            users['email'] = email

    return {}

def user_profile_sethandle(token, handle_str):
    '''
    user_profile_sethandle 

    Args:
        token: authorises user
        handle_str: new handle to be updated 

    Returns: 
        returns {}

    Raises: 
        InputError when handle_str not between 3 and 20 characters
        InputError when handle is already in use by any registered user.
        AccessError when token is not valid
    '''
    # Validating the token of the user and finds corresponding user.
    user = token_validator(token)

    # Checks to see if handle is between 3 and 20 characters.
    if len(handle_str) <= 3:
        raise InputError("The new handle you are updating must be greater than 3 characters.")
    if len(handle_str) >= 20:
        raise InputError("The new handle you are updating must be less than than 20 characters.")
    
    # Checks to see if handle is already in use.
    for users in data['users']:
        if handle_str == users['handle_str']:
            raise InputError("The handle you entered is already in use.")
    
    # Updates the handle to the new handle specified.
    for users in data['users']:
        if users['u_id'] == user['u_id']:
            users['handle_str'] = handle_str

    return {}

def user_profile_uploadphoto(token, img_url, x_start, y_start, x_end, y_end):
    '''
    user_profile_uploadphoto 

    Args:
        token: authorises user.
        img_url: The url of the source image is provided.
        x_start, y_start, x_end, y_end: Image dimensions are specified by the user.

    Returns: 
        returns {}

    Raises:
        AccessError when the token is invalid
        InputError when img_url returns an HTTP status other than 200.
        InputError when any of the parameters are not within the dimensions of the image at the URL.
        InputError when the image uploaded is not a JPG
    '''

    user = token_validator(token)

    # Verify that the img_url is valid
    r = requests.head(img_url)
    valid_url = r.status_code == 200
    if not valid_url:
        raise InputError("The image url returned a HTTP status other than 200.")
    
    # Verify that the image has JPG format
    image = imgspy.info(img_url)
    if image['type'] == None or image['type'] != 'jpg':
        raise InputError("Image uploaded is not a JPG.")

    # Verify that the parameters are within image dimensions
    # {'type': 'jpg', 'width': 2370, 'height': 1927}
    img_width = range(0, image['width'] + 1)
    img_height = range(0, image['height'] + 1)

    if (x_start in img_width and x_end in img_width
    and y_start in img_height and y_end in img_height):
        print("valid")
    else:
        raise InputError("x_start, y_start, x_end, y_end are not within \
                          the dimensions of the image at the URL.")

    # Generate unique image_id using uuid
    profile_img_url = str(uuid.uuid4())

    # Download and retrieve the image
    profile_image = f"{IMG_LOCATION}/{profile_img_url}.jpg"

    # Move the image into the appropriate directory
    urllib.request.urlretrieve(img_url, profile_image)

    # Crop the image
    imageObject = Image.open(profile_image)
    cropped = imageObject.crop((x_start, y_start, x_end, y_end))
    cropped.save(profile_image)

    # Add image url to the user's data
    for users in data['users']:
        if users['u_id'] == user['u_id']:
            users['profile_img_url'] = profile_img_url + '.jpg'

    return {}
