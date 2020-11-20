""" DUMMY EXAMPLE
data = {
    'users': [
        {
            'u_id': 0,
            'email': 'example@gmail.com',
            'handle_str': 'johndoe',
            'password': '<hashed password>',
            'name_first': 'John',
            'name_last': 'Doe',
            'profile_img_url': 'default.jpg',
            'permission_id': 1, # (1 is Flockr owner) (2 is Flockr member)
        },
    ],
    'channels': [
        {
            'channel_id': 0,
            'name': 'channel_example',
            'owner_members': [2,4,6],
            'all_members': [2,4,6,7,8],
            'is_public': False,
            'time_finish': None,
            'messages': [
                {
                    'message_id': 0,
                    'u_id: 0,
                    'message': 'Example Message',
                    'time_created': 12345,
                    'reacts': [
                        {
                            'react_id': 0,
                            'u_ids': [0, 1, 2],
                            'is_this_user_reacted': False,
                        }
                    ],
                    'is_pinned': False
                }
            ]
        }
    ],
    'message_counter': 0,
}
"""

data = {
    'users': [],
    'channels': [],
    'message_counter': 0,
}
