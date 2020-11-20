"""
user_profile_uploadphoto_test.py

Fixtures:
    register_login: Registers and logs a user in.
    img: Referring to the IMG_URL, returns details about image dimensions and type

Test Modules:
- Invalid Cases
    test_invalid_token: AccessError - Invalid Token.
    test_invalid_img_type: InputError - Image uploaded is not a JPG.
    test_invalid_x_start: InputError - x_start is not within the dimensions of the image at the URL.
    test_invalid_y_start: InputError - y_start is not within the dimensions of the image at the URL.
    test_invalid_x_end: InputError - x_end is not within the dimensions of the image at the URL.
    test_invalid_y_end: InputError - y_end is not within the dimensions of the image at the URL.

- Success Cases
    test_img_upload: Ensure that no errors are raised on successful upload.
    test_img_crop: Ensure that no errors are raised when image is cropped.
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))

import pytest
import imgspy
from implement.other              import clear
from helper             import token_hash
from error              import AccessError, InputError
from implement.auth     import auth_register, auth_login

from implement.user    import user_profile_uploadphoto

# Image dimensions for this photo are: 2370 x 1927
# i.e. (0, 0, 2370, 1927)
IMG_URL = 'https://upload.wikimedia.org/wikipedia/commons/a/a3/June_odd-eyed-cat.jpg'
INVALID_IMG_TYPE = 'https://freepngimg.com/thumb/cat/19-cat-png-image-download-picture-kitten-thumb.png'
INVALID_IMG_URL = 'https://www.unsw.edu.au/%'

@pytest.fixture
def register_login():
    # A user is registered, logged in and owns a channel
    clear()

    # Dummy 
    auth_register("dummy@email.com", "password", "Antomum", "Lepejian")

    auth_register("owner@email.com", "password", "Anto", "Lepejian")
    owner = auth_login("owner@email.com", "password")

    return {
        'u_id': owner['u_id'], 
        'token': owner['token'],
    }

@pytest.fixture
def img():
    image = imgspy.info(IMG_URL)

    return {
        'type': image['type'],
        'x_start': 0,
        'y_start': 0,
        'x_end': image['width'],
        'y_end': image['height'],
    }

'''Invalid Cases'''
def test_invalid_token(register_login, img):
    invalid_token = token_hash(-1)

    with pytest.raises(AccessError):
        user_profile_uploadphoto(
            invalid_token, 
            IMG_URL, 
            img['x_start'], 
            img['y_start'], 
            img['x_end'], 
            img['y_end'],
        )
    pass

# InputError: Image uploaded is not a JPG
def test_invalid_img_type(register_login, img):
    owner = register_login

    with pytest.raises(InputError):
        user_profile_uploadphoto(
            owner['token'],
            INVALID_IMG_TYPE,
            img['x_start'], 
            img['y_start'], 
            img['x_end'], 
            img['y_end'],
        )

def test_invalid_img_url(register_login, img):
    owner = register_login

    with pytest.raises(InputError):
        user_profile_uploadphoto(
            owner['token'],
            INVALID_IMG_URL,
            img['x_start'], 
            img['y_start'], 
            img['x_end'], 
            img['y_end'],
        )

def test_invalid_x_start(register_login, img):
    owner = register_login
    invalid_x_start = -1

    with pytest.raises(InputError):
        user_profile_uploadphoto(
            owner['token'], 
            IMG_URL, 
            invalid_x_start, 
            img['y_start'], 
            img['x_end'], 
            img['y_end'],
        )
    pass

def test_invalid_y_start(register_login, img):
    owner = register_login
    invalid_y_start = -1

    with pytest.raises(InputError):
        user_profile_uploadphoto(
            owner['token'], 
            IMG_URL, 
            img['x_start'], 
            invalid_y_start, 
            img['x_end'], 
            img['y_end'],
        )
    pass

def test_invalid_x_end(register_login, img):
    owner = register_login
    invalid_x_end = 1 + img['x_end']

    with pytest.raises(InputError):
        user_profile_uploadphoto(
            owner['token'], 
            IMG_URL, 
            img['x_start'], 
            img['y_start'], 
            invalid_x_end, 
            img['y_end'],
        )
    pass

def test_invalid_y_end(register_login, img):
    owner = register_login
    invalid_y_end = 1 + img['y_end']

    with pytest.raises(InputError):
        user_profile_uploadphoto(
            owner['token'], 
            IMG_URL, 
            img['x_start'], 
            img['y_start'], 
            img['x_end'], 
            invalid_y_end,
        )
    pass

'''Success Cases'''
def test_img_upload(register_login, img):
    owner = register_login

    assert user_profile_uploadphoto(
            owner['token'], 
            IMG_URL, 
            img['x_start'], 
            img['y_start'], 
            img['x_end'], 
            img['y_end'],
    ) == {}

def test_img_crop(register_login, img):
    owner = register_login
    crop_x = 1700
    crop_y = 1725

    assert user_profile_uploadphoto(
            owner['token'], 
            IMG_URL, 
            img['x_start'], 
            img['y_start'], 
            crop_x, 
            crop_y,
    ) == {}

if __name__ == '__main__':
    test_img_upload
    owner = register_login()
    img = img()

    user_profile_uploadphoto(
            owner['token'], 
            IMG_URL, 
            img['x_start'], 
            img['y_start'], 
            img['x_end'], 
            img['y_end'],
    )
