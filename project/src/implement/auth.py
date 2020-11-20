"""
auth.py

Helper Modules:
    check: Checks if email is valid using method provided in spec
    unique_handle: Checks to see if default generated handle exists

Main Modules:
    auth_login: logs a registered user in
    auth_logout: logs a registered user out
    auth_register: registers a new user 
    auth_passwordreset_request: sends user a code to reset password through their email
    auth_passwordreset_reset: resets the user's password
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

from data               import data
from error              import InputError, AccessError
from helper             import token_validator, token_hash, password_hash
import jwt, smtplib, ssl, re   

# Checks if email is valid using method provided
def check(email): 
    regex = r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
    if (re.search(regex,email)):
        return True 
    else: 
        return False

def auth_login(email, password):
    '''
    auth_login

    Args: 
        email: user email
        password: user password

    Returns:
        a dictionary containing users u_id and their token 
    '''

    password = password_hash(password)
    valid_email = check(email)
    
    if valid_email == True:
        for user in data['users']:
            if email == user['email'] and password == user['password']:
                u_id = user['u_id']
                email = user['email']

                return {'u_id': u_id, 'token': token_hash(u_id)}
        raise InputError("Either the email was not registered or the password is wrong.")
    
    raise InputError("Email entered is not a valid email.")

def auth_logout(token):
    '''
    auth_logout

    Args: 
        token: user token for the session 

    Returns:
        a dictionary containing 'is_success': their token  
    
    Raises:
        AccessError when token is invalid
    '''

    # since token_validator may raise error, need to catch it and return false when hapens
    try:
        token_validator(token)
    except AccessError:
        return {'is_success': False}

    return {'is_success': True}

def auth_register(email, password, name_first, name_last):
    '''
    auth_register

    Args: 
        email: user email
        password: user password
        name_first: user firt name
        name_last: user last name

    Returns:
        a dictionary containing users u_id and their token   
    '''

    valid_email = check(email)  
    
    unique_email = True 
    for user in data['users']:
        if email == user['email']:
            unique_email = False
    
    pw_len = len(password) >= 6
    
    fname_len = 1 <= len(name_first) <= 50

    lname_len = 1 <= len(name_last) <= 50

    if not valid_email:
        raise InputError("Email entered is not a valid email using the method provided.")
    elif not unique_email:
        raise InputError("Email address is already being used by another user.")
    elif not pw_len:
        raise InputError("Password entered is less than 6 characters long.")
    elif not fname_len:
        raise InputError("name_first not is between 1 and 50 characters inclusively in length.")
    elif not lname_len:
        raise InputError("name_last is not between 1 and 50 characters inclusively in length.")

    if not len(data['users']):
        u_id = 0
    else: 
        for user in data['users']:
            last_u_id = user['u_id']
            u_id = last_u_id + 1
    handle = name_first.lower() + name_last.lower()

    # Checks to see if concatenation of first and last name already exists
    # If it does, add the u_id to start of handle to make it unique.
    if not unique_handle(handle):
        handle = str(u_id) + name_first.lower() + name_last.lower()
    handle = handle[:20]

    # Determine if Flockr owner or not, first user is Flockr Owner
    permission_id = 2
    if u_id == 0:
        permission_id = 1

    # Hash the password after completing password checks for the user
    password = password_hash(password)

    new_user = {
            'u_id': u_id,
            'email': email,
            'handle_str': handle,
            'password': password,
            'name_first': name_first,
            'name_last': name_last,
            'profile_img_url': 'default.jpg',
            'permission_id': permission_id,
        }
    new_user_copy = new_user.copy()
    data['users'].append(new_user_copy)

    return {
        'u_id': u_id,
        'token': token_hash(u_id),
    }

# Checks to see if default generated handle exists
def unique_handle(handle):
    for user in data['users']:
        if user['handle_str'] == handle:
            return False
    return True

def auth_passwordreset_request(email):
    '''
    auth_passwordreset_request

    Args: 
        email: user email

    Returns:
        {} always   
    '''
    email_exists = False
    for users in data['users']:
        if email == users['email']:
            email_exists = True
    
    if not email_exists:
        return {}        

    SECRET = 'BSOC4THEBOYS'
    encoded_jwt = jwt.encode({"email": email}, SECRET, algorithm = 'HS256')
    code = encoded_jwt.decode('utf-8')

    port = 465  
    smtp_server = "smtp.gmail.com"
    sender_email = "1531mangoteam3@gmail.com"  
    receiver_email = email
    password = 'wz"b9Tu@}gCWF_+F'
    message = f"""\
Subject: Your Flockr Password Reset Code

Use this code to reset your Flockr account password:
{code}"""

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)

    return {}

def auth_passwordreset_reset(reset_code, new_password):
    '''
    auth_passwordreset_reset

    Args:
        reset_code: encoded code which is sent to the users email
        new_password: the new password

    Returns:
        {}
    Raises:
        InputError when reset_code is not valid for that user
        InputError when the new password is not valid (less than six characters)
    '''

    SECRET = 'BSOC4THEBOYS'
    encoded_jwt = reset_code.encode('utf-8')
    decoded_jwt = jwt.decode(encoded_jwt, SECRET, algorithms=['HS256'])

    pw_length = len(new_password) > 6

    # Check for password length is valid
    if not pw_length:
        raise InputError("New Password entered is less than 6 characters long")  

    for user in data['users']:
        if decoded_jwt['email'] == user['email']:
            user['password'] = password_hash(new_password)
            return {}
    
    raise InputError("Reset Code is not a valid reset code")
