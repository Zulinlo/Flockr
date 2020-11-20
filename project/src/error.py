"""
error.py

Main Modules:
    AccessError: raised when the user isn't authorised to acccess the function or information
    InputError: raised when the input to a function isn't valid
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

from werkzeug.exceptions import HTTPException

class AccessError(HTTPException):
    code = 400
    message = 'No message specified'

class InputError(HTTPException):
    code = 400
    message = 'No message specified'
