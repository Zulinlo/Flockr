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

import re
import signal
import json
import requests
import urllib
from subprocess     import Popen, PIPE
from time           import sleep

import pytest
import imgspy
from helper     import token_hash

# Image dimensions for this photo are: 2370 x 1927
# i.e. (0, 0, 2370, 1927)
IMG_URL = 'https://upload.wikimedia.org/wikipedia/commons/a/a3/June_odd-eyed-cat.jpg'
INVALID_IMG_TYPE = 'https://freepngimg.com/thumb/cat/19-cat-png-image-download-picture-kitten-thumb.png'
INVALID_IMG_URL = 'https://www.unsw.edu.au/%'

@pytest.fixture
def url():
    url_re = re.compile(r' \* Running on ([^ ]*)')
    server = Popen(["python3", "src/server.py"], stderr=PIPE, stdout=PIPE)
    line = server.stderr.readline()
    local_url = url_re.match(line.decode())
    if local_url:
        yield local_url.group(1)
        # Terminate the server
        server.send_signal(signal.SIGINT)
        waited = 0
        while server.poll() is None and waited < 5:
            sleep(0.1)
            waited += 0.1
        if server.poll() is None:
            server.kill()
    else:
        server.kill()
        raise Exception("Couldn't get URL from local server")

@pytest.fixture
def register_login(url):
    # A user is registered, logged in and owns a channel
    requests.delete(f"{url}/clear")
    requests.post(f"{url}/auth/register", json={
        "email":"owner@gmail.com", 
        "password": "password", 
        "name_first": "Anto",
        "name_last": "Lepejian",
    })
    r = requests.post(f"{url}/auth/login", json={
        "email":"owner@gmail.com", 
        "password": "password"
    })
    owner = r.json()

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
def test_invalid_token(url, register_login, img):
    invalid_token = token_hash(-1)

    # with pytest.raises(AccessError):
    r = requests.post(f"{url}/user/profile/uploadphoto", json={
        "token": invalid_token, 
        "img_url": IMG_URL, 
        "x_start": img['x_start'], 
        "y_start": img['y_start'],
        "x_end": img['x_end'],
        "y_end": img['y_end'],
        
    })
    payload = r.json()
    print(payload)
    assert payload['code'] == 400

# InputError: Image uploaded is not a JPG
def test_invalid_img_type(url, register_login, img):
    owner = register_login

    r = requests.post(f"{url}/user/profile/uploadphoto", json={
        "token": owner['token'], 
        "img_url": INVALID_IMG_TYPE, 
        "x_start": img['x_start'],
        "y_start": img['y_start'],
        "x_end": img['x_end'],
        "y_end": img['y_end'],
    })
    payload = r.json()
    assert payload['code'] == 400

def test_invalid_img_url(url, register_login, img):
    owner = register_login

    r = requests.post(f"{url}/user/profile/uploadphoto", json={
        "token": owner['token'], 
        "img_url": INVALID_IMG_URL,
        "x_start": img['x_start'], 
        "y_start": img['y_start'],
        "x_end": img['x_end'],
        "y_end": img['y_end'],
    })
    payload = r.json()
    assert payload['code'] == 400

def test_invalid_x_start(url, register_login, img):
    owner = register_login
    invalid_x_start = -1

    r = requests.post(f"{url}/user/profile/uploadphoto", json={
        "token": owner['token'], 
        "img_url": IMG_URL, 
        "x_start": invalid_x_start, 
        "y_start": img['y_start'],
        "x_end": img['x_end'],
        "y_end": img['y_end'],
    })
    payload = r.json()
    assert payload['code'] == 400

def test_invalid_y_start(url, register_login, img):
    owner = register_login
    invalid_y_start = -1

    r = requests.post(f"{url}/user/profile/uploadphoto", json={
        "token": owner['token'], 
        "img_url": IMG_URL, 
        "x_start": img['x_start'], 
        "y_start": invalid_y_start,
        "x_end": img['x_end'],
        "y_end": img['y_end'],
    })
    payload = r.json()
    assert payload['code'] == 400

def test_invalid_x_end(url, register_login, img):
    owner = register_login
    invalid_x_end = 1 + img['x_end']

    r = requests.post(f"{url}/user/profile/uploadphoto", json={
        "token": owner['token'], 
        "img_url": IMG_URL, 
        "x_start": img['x_start'], 
        "y_start": img['y_start'],
        "x_end": invalid_x_end,
        "y_end": img['y_end'],
    })
    payload = r.json()
    assert payload['code'] == 400

def test_invalid_y_end(url, register_login, img):
    owner = register_login
    invalid_y_end = 1 + img['y_end']

    r = requests.post(f"{url}/user/profile/uploadphoto", json={
        "token": owner['token'], 
        "img_url": IMG_URL, 
        "x_start": img['x_start'], 
        "y_start": img['y_start'],
        "x_end": img['x_end'],
        "y_end": invalid_y_end,
    })
    payload = r.json()
    assert payload['code'] == 400

'''Success Cases'''
def test_img_upload(url, register_login, img):
    owner = register_login
    print(img['x_start'])
    r = requests.post(f"{url}/user/profile/uploadphoto", json={
        "token": owner['token'], 
        "img_url": IMG_URL, 
        "x_start": img['x_start'], 
        "y_start": img['y_start'],
        "x_end": img['x_end'],
        "y_end": img['y_end'],
    })
    payload = r.json()
    assert payload == {}

def test_img_crop(url, register_login, img):
    owner = register_login
    crop_x = 1700
    crop_y = 1725

    r = requests.post(f"{url}/user/profile/uploadphoto", json={
        "token": owner['token'], 
        "img_url": IMG_URL, 
        "x_start": img['x_start'], 
        "y_start": img['y_start'],
        "x_end": crop_x,
        "y_end": crop_y,
    })
    payload = r.json()
    assert payload == {}

# if __name__ == '__main__':
#     owner = register_login()
#     img = img()
#     crop_x = 1700
#     crop_y = 1725

#     assert user_profile_uploadphoto(
#             owner['token'], 
#             IMG_URL, 
#             img['x_start'], 
#             img['y_start'], 
#             crop_x, 
#             crop_y,
#     ) == {}
#     pass
