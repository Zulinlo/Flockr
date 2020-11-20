"""
server.py
    - provides HTTPS routes for all modules
"""
# Import paths for json and HTTP
import sys
import os
from json       import dumps
from flask      import Flask, request, send_from_directory, abort
from flask_cors import CORS
from error      import InputError

# Import paths for main modules
import implement.message  as m
import implement.auth     as a
import implement.channel  as c
import implement.channels as cs
import implement.user     as u
import implement.other    as o
import implement.standup  as s

def defaultHandler(err):
    response = err.get_response()
    print('response', err, err.get_response())
    response.data = dumps({
        "code": err.code,
        "name": "System Error",
        "message": err.get_description(),
    })
    response.content_type = 'application/json'
    return response

APP = Flask(__name__, static_url_path='/static/')
CORS(APP)

APP.config['TRAP_HTTP_EXCEPTIONS'] = True

# The absolute path of the directory containing images for users to download
APP.config["CLIENT_IMAGES"] = f"{os.getcwd()}/src/profile_pictures"

APP.register_error_handler(Exception, defaultHandler)

# ===================================================
#  _____     _            ______            _       
# |  ___|   | |           | ___ \          | |      
# | |__  ___| |__   ___   | |_/ /___  _   _| |_ ___ 
# |  __|/ __| '_ \ / _ \  |    // _ \| | | | __/ _ \
# | |__| (__| | | | (_) | | |\ \ (_) | |_| | ||  __/
# \____/\___|_| |_|\___/  \_| \_\___/ \__,_|\__\___|

# ===================================================

@APP.route("/echo", methods=['GET'])
def echo():
    data = request.args.get('data')
    if data == 'echo':
   	    raise InputError(description='Cannot echo "echo"')
    return dumps({
        'data': data
    })

# =========================================================
#   ___        _   _      ______            _
#  / _ \      | | | |     | ___ \          | |
# / /_\ \_   _| |_| |__   | |_/ /___  _   _| |_ ___  ___
# |  _  | | | | __| '_ \  |    // _ \| | | | __/ _ \/ __|
# | | | | |_| | |_| | | | | |\ \ (_) | |_| | ||  __/\__ \
# \_| |_/\__,_|\__|_| |_| \_| \_\___/ \__,_|\__\___||___/

# =========================================================

@APP.route("/auth/login", methods=['POST'])
def auth_login_flask():
    payload = request.get_json()

    email = payload['email']
    password = payload['password']

    return dumps(
        a.auth_login(email, password)
    )

@APP.route("/auth/logout", methods=['POST'])
def auth_logout_flask():
    payload = request.get_json()

    token = payload['token']

    return dumps(
        a.auth_logout(token)
    )

@APP.route("/auth/register", methods=['POST'])
def auth_register_flask():
    payload = request.get_json()

    email = payload['email']
    password = payload['password']
    name_first = payload['name_first']
    name_last = payload['name_last']

    return dumps(
        a.auth_register(email, password, name_first, name_last)
    )

@APP.route("/auth/passwordreset/request", methods=['POST'])
def auth_passwordreset_request_flask():
    payload = request.get_json()
    email = payload['email']
    return dumps(
        a.auth_passwordreset_request(email)
    )

@APP.route("/auth/passwordreset/reset", methods=['POST'])
def auth_passwordreset_reset_flask():

    payload = request.get_json()
    reset_code = payload['reset_code']
    new_password = payload['new_password']

    return dumps(
        a.auth_passwordreset_reset(reset_code, new_password)
    )
    
# =======================================================================
#  _____ _                            _  ______            _
# /  __ \ |                          | | | ___ \          | |
# | /  \/ |__   __ _ _ __  _ __   ___| | | |_/ /___  _   _| |_ ___  ___
# | |   | '_ \ / _` | '_ \| '_ \ / _ \ | |    // _ \| | | | __/ _ \/ __|
# | \__/\ | | | (_| | | | | | | |  __/ | | |\ \ (_) | |_| | ||  __/\__ \
#  \____/_| |_|\__,_|_| |_|_| |_|\___|_| \_| \_\___/ \__,_|\__\___||___/

# =======================================================================

@APP.route("/channel/invite", methods=['POST'])
def channel_invite_flask():
    payload = request.get_json()

    token = payload['token']
    channel_id = payload['channel_id']
    u_id = payload['u_id']

    return dumps(
        c.channel_invite(token, channel_id, u_id)
    )

@APP.route("/channel/details", methods=['GET'])
def channel_details_flask():
    token = request.args.get('token')
    channel_id = int(request.args.get('channel_id'))
    result = c.channel_details(token, channel_id)

    for user in result['owner_members']:
        user['profile_img_url'] = 'http://' + str(request.host) + '/profile_pictures/' + str(user['profile_img_url'])

    for user in result['all_members']:
        user['profile_img_url'] = 'http://' + str(request.host) + '/profile_pictures/' + str(user['profile_img_url'])

    return dumps(
        result
    )

@APP.route("/channel/messages", methods=['GET'])
def channel_messages_flask():
    token = request.args.get('token')
    channel_id = int(request.args.get('channel_id'))
    start = int(request.args.get('start'))

    return dumps(
        c.channel_messages(token, channel_id, start))
    
@APP.route("/channel/leave", methods=['POST'])
def channel_leave_flask():
    payload = request.get_json()
    token = payload['token']
    channel_id = payload['channel_id']
    return dumps(
        c.channel_leave(token, channel_id)
    )

@APP.route("/channel/join", methods=['POST'])
def channel_join_flask():
    payload = request.get_json()
    token = payload['token']
    channel_id = payload['channel_id']
    return dumps(
        c.channel_join(token, channel_id)
    )

@APP.route("/channel/addowner", methods=['POST'])
def channel_addowner_flask():
    payload = request.get_json()

    token = payload['token']
    channel_id = payload['channel_id']
    u_id = payload['u_id']
    return dumps(
        c.channel_addowner(token, channel_id, u_id)
    )

@APP.route("/channel/removeowner", methods=['POST'])
def channel_removeowner_flask():
    payload = request.get_json()

    token = payload['token']
    channel_id = payload['channel_id']
    u_id = payload['u_id']
    return dumps(
        c.channel_removeowner(token, channel_id, u_id)
    )

# ===========================================================================
#  _____ _                            _      ______            _            
# /  __ \ |                          | |     | ___ \          | |           
# | /  \/ |__   __ _ _ __  _ __   ___| |___  | |_/ /___  _   _| |_ ___  ___ 
# | |   | '_ \ / _` | '_ \| '_ \ / _ \ / __| |    // _ \| | | | __/ _ \/ __|
# | \__/\ | | | (_| | | | | | | |  __/ \__ \ | |\ \ (_) | |_| | ||  __/\__ \
#  \____/_| |_|\__,_|_| |_|_| |_|\___|_|___/ \_| \_\___/ \__,_|\__\___||___/

# ===========================================================================

@APP.route("/channels/list", methods=['GET'])
def channels_list_flask():
    token = request.args.get('token')
    
    return dumps(
        cs.channels_list(token)
    )

@APP.route("/channels/listall", methods=['GET'])
def channels_listall_flask():
    token = request.args.get('token')

    return dumps(
        cs.channels_listall(token)
    )

@APP.route("/channels/create", methods=['POST'])
def channels_create_flask():
    payload = request.get_json()

    token = payload['token']
    name = payload['name']
    is_public = payload['is_public']

    return dumps(
        cs.channels_create(token, name, is_public)
    )

# ========================================================================
# ___  ___                                ______            _
# |  \/  |                                | ___ \          | |
# | .  . | ___  ___ ___  __ _  __ _  ___  | |_/ /___  _   _| |_ ___  ___
# | |\/| |/ _ \/ __/ __|/ _` |/ _` |/ _ \ |    // _ \| | | | __/ _ \/ __|
# | |  | |  __/\__ \__ \ (_| | (_| |  __/ | |\ \ (_) | |_| | ||  __/\__ \
# \_|  |_/\___||___/___/\__,_|\__, |\___| \_| \_\___/ \__,_|\__\___||___/
                             # __/ |
                            # |___/
# ========================================================================

@APP.route("/message/send", methods=['POST'])
def message_send_flask():
    payload = request.get_json()

    token = payload['token']
    channel_id = int(payload['channel_id'])
    message = payload ['message']

    return dumps(
        m.message_send(token, channel_id, message)
    )

@APP.route("/message/remove", methods=['DELETE'])
def message_remove_flask():
    payload = request.get_json()

    token = payload['token']
    message_id = payload['message_id']

    return dumps(
        m.message_remove(token, message_id)
    )

@APP.route("/message/edit", methods=['PUT'])
def message_edit_flask():
    payload = request.get_json()

    token = payload['token']
    message_id = payload['message_id']
    message = payload['message']

    return dumps(
        m.message_edit(token, message_id, message)
    )

@APP.route("/message/pin", methods=['POST'])
def message_pin_flask():
    payload = request.get_json()

    token = payload['token']
    message_id = payload['message_id']

    return dumps(
        m.message_pin(token, message_id)
    )

@APP.route("/message/unpin", methods=['POST'])
def message_unpin_flask():
    payload = request.get_json()

    token = payload['token']
    message_id = payload['message_id']

    return dumps(
        m.message_unpin(token, message_id)
    )

@APP.route("/message/react", methods=['POST'])
def message_react_flask():
    payload = request.get_json()

    token = payload['token']
    message_id = payload['message_id']
    react_id = payload['react_id']

    return dumps(
        m.message_react(token, message_id, react_id)
    )


@APP.route("/message/unreact", methods=['POST'])
def message_unreact_flask():
    payload = request.get_json()
    token = payload['token']
    message_id = payload['message_id']
    react_id = payload['react_id']

    return dumps(
        m.message_unreact(token, message_id, react_id)
    )

@APP.route("/message/sendlater", methods=['POST'])
def message_sendlater_flask():
    payload = request.get_json()

    token = payload['token']
    channel_id = payload['channel_id']
    message = payload['message']
    time_sent = payload['time_sent']

    return dumps(
        m.message_sendlater(token, channel_id, message, time_sent)
    )

# ======================================================
#  _   _                ______            _            
# | | | |               | ___ \          | |           
# | | | |___  ___ _ __  | |_/ /___  _   _| |_ ___  ___ 
# | | | / __|/ _ \ '__| |    // _ \| | | | __/ _ \/ __|
# | |_| \__ \  __/ |    | |\ \ (_) | |_| | ||  __/\__ \
#  \___/|___/\___|_|    \_| \_\___/ \__,_|\__\___||___/
                                                     
# ======================================================

@APP.route("/user/profile", methods=['GET'])
def user_profile_flask():
    token = request.args.get('token')
    u_id = int(request.args.get('u_id'))
    result = u.user_profile(token, u_id)
    result['user']['profile_img_url'] = 'http://' + str(request.host) + '/profile_pictures/' + str(result['user']['profile_img_url'])
    return dumps(
        result
    )

@APP.route("/user/profile/setname", methods=['PUT'])
def user_profile_setemail_flask():
    payload = request.get_json()
    token = payload['token']
    name_first = payload['name_first']
    name_last = payload['name_last']

    return dumps(
        u.user_profile_setname(token, name_first, name_last)
    )

@APP.route("/user/profile/setemail", methods=['PUT'])
def user_profile__setemail_flask():
    payload = request.get_json()
    token = payload['token']
    email = payload['email']

    return dumps(
        u.user_profile_setemail(token, email)
    )

@APP.route("/user/profile/sethandle", methods=['PUT'])
def user_profile__sethandle_flask():
    payload = request.get_json()
    token = payload['token']
    handle_str = payload['handle_str']

    return dumps(
        u.user_profile_sethandle(token, handle_str)
    )

@APP.route("/user/profile/uploadphoto", methods=['POST'])
def user_profile_sethandle_flask():
    payload = request.get_json()

    token = payload['token']    
    img_url = payload['img_url']
    x_start = payload['x_start']
    y_start = payload['y_start']
    x_end = payload['x_end']
    y_end = payload['y_end']

    return dumps(
        u.user_profile_uploadphoto(token, img_url, x_start, y_start, x_end, y_end)
    )

@APP.route("/profile_pictures/<image_url>", methods=['GET'])
def user_profile_getphoto_flask(image_url):
    # Fetch image object based on route
    try:
        return send_from_directory(APP.config["CLIENT_IMAGES"], filename=image_url, as_attachment=True)
    except FileNotFoundError:
        abort(404)

@APP.route('/profile_pictures/<path:path>')
def send_js(path):
    return send_from_directory('', path)

# ===========================================================
#  _____ _   _                ______            _
# |  _  | | | |               | ___ \          | |
# | | | | |_| |__   ___ _ __  | |_/ /___  _   _| |_ ___  ___
# | | | | __| '_ \ / _ \ '__| |    // _ \| | | | __/ _ \/ __|
# \ \_/ / |_| | | |  __/ |    | |\ \ (_) | |_| | ||  __/\__ \
#  \___/ \__|_| |_|\___|_|    \_| \_\___/ \__,_|\__\___||___/

# ===========================================================

@APP.route("/users/all", methods=['GET'])
def users_all_flask():
    token = request.args.get('token')
    result = o.users_all(token)
    for user in result['users']:
        user['profile_img_url'] = 'http://' + str(request.host) + '/profile_pictures/' + str(user['profile_img_url'])
    return dumps(
        result
    )

@APP.route("/admin/userpermission/change", methods=['POST'])
def admin_userpermission_change_flask():
    payload = request.get_json()

    token = payload['token']
    u_id = payload['u_id']
    permission_id = payload['permission_id']

    return dumps(
        o.admin_userpermission_change(token, u_id, permission_id)
    )

@APP.route("/search", methods=['GET'])
def other_search_flask():
    token = request.args.get('token')
    query_str = request.args.get('query_str')

    return dumps(
        o.search(token, query_str)
    )

@APP.route("/clear", methods=['DELETE'])
def clear_flask():
    return dumps(
        o.clear()
    )

# ==========================================================================
#  _____ _                  _              ______            _            
# /  ___| |                | |             | ___ \          | |           
# \ `--.| |_ __ _ _ __   __| |_   _ _ __   | |_/ /___  _   _| |_ ___  ___ 
#  `--. \ __/ _` | '_ \ / _` | | | | '_ \  |    // _ \| | | | __/ _ \/ __|
# /\__/ / || (_| | | | | (_| | |_| | |_) | | |\ \ (_) | |_| | ||  __/\__ \
# \____/ \__\__,_|_| |_|\__,_|\__,_| .__/  \_| \_\___/ \__,_|\__\___||___/
                                 # | |                                    
                                 # |_|                                    
# ==========================================================================

@APP.route("/standup/start", methods=['POST'])
def standup_start_flask():
    payload = request.get_json()

    token = payload['token']
    channel_id = payload['channel_id']
    length = payload['length']

    return dumps(
        s.standup_start(token, channel_id, length)
    )

@APP.route("/standup/active", methods=['GET'])
def standup_active_flask():
    token = request.args.get('token')
    channel_id = int(request.args.get('channel_id'))

    return dumps(
        s.standup_active(token, channel_id)
    )

@APP.route("/standup/send", methods=['POST'])
def standup_send_flask():
    payload = request.get_json()

    token = payload['token']
    channel_id = payload['channel_id']
    message = payload['message']

    return dumps(
        s.standup_send(token, channel_id, message)
    )


if __name__ == "__main__":
    APP.run(port=0) # Do not edit this port
