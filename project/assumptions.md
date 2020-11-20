### ASSUMPTIONS ###

# Overall Assumptions
Authorisation
- Token is not appended to the active token list if log-in fails
- Token is jwt encoded with payload being {'u\_id': u\_id}
  validates user by checking against payload using SECRET

Channels
- Channel owners are a subcategory of members

## Assumptions for features ##
# Auth.py
auth\_login():
- When the user logs in, the token is attached to them, and follows them wherever they go, and enter which functions (e.g. channels\_createl or channel\_join)
- Returns jwt token

auth\_logout():
- If the user has an invalid token, they cannot logout since their account never existed
- If the user logs out successfully, their token will be null and they cannot pass that token into other functions as they will cause errors via the token\_validator which is called at the start of each function

auth\_register():
- Uses token which is a jwt token using the secret "shenpai", payload of u\_id
- The first person to register gets a u\_id of 0, every subsequent member that registers get’s assigned the u\_id equal to the last registered member’s u\_id + 1.
- First person to register is the flockr owner
- Register also adds default.jpg which is a picture of a well dressed young gentleman

auth\_passwordreset\_request():
- Only emails entered that have been registered will receive an email
- Will show success even though email may not exist, but if email doesn't exist, email won't be sent.

auth\_passwordreset\_reset():
- The user may reset their password to the password that was already in use
- Unregistered users are not able to gain access to a code
- If reset code doesn’t correspond to a registered user, error is thrown.
- New password must be greater than 6 characters long, same as when registering a new user.

# Channel.py
channel\_invite():
- That channel invites can be given to any user from any type of channel whether it be public or private
- Channel invites can only be given by channel owners and not any general member

channel\_details():
- ‘Basic channel details’ as referred to in the spec is assumed to be name of channel, owner\_members, and all\_members, with members having their first name and last name listed too. 

channel\_messages():
- The start input is of int type
- That the messages are never deleted within iteration 1 as the module loops through the messages within a channel and increments accordingly, 
- The increment of inputting messages does not change from 0++ path

channel\_leave():
- If channel owners leave a channel, the channel still exists (Allows other people to still join the channel even if it is empty)
- If channel owners leave, they are removed from both all\_members and owner\_members set

channel\_join():
- That the channel can be either public or private
- That any non channel member can join the channel

channel\_addowner():
- A newly joined member cannot have the ability to make another member an owner
- The owner cannot add another member as an owner, if they are already an owner

channel\_removeowner():
- Only an owner can remove other owners from the channel
- There always has to be at least one owner in the channel at a moment in time. I.e. an owner cannot run channel\_removeowner.
- If there was a channel with no owners, it would be impossible to add an owner in the channel since you need to be an owner to add an owner.


# Channels.py
channels\_list():
- When called, every channel key and corresponding details are listed and not None
- If the token passed through is invalid, returns AccessError
- If user belongs to no channel, return nothing rather than an error

channels\_listall():
- When called, every single key and corresponding value stored in the data dictionary for the channels are listed.
- If the token passed through is invalid, returns AccessError.

channels\_create():
- Is\_public has to be either True or False and can't be None
- The channel name can consist of any special characters

# User.py
user\_profile():
- The user calling the function must be already registered and logged in.

user\_profile\_setname():
- The user's name first and last can be any special character as long as its within the character length
- The token has to belong to an existing user

user\_profile\_setemail():
- The updated email cannot be invalid, thus, has to have proper syntax e.g. '@' and '.'
- If the updated email is the same as a preexisting email, it will raise an InputError
- The email cannot be updated if the preexisting error was never valid

user\_profile\_sethandle():
- The new handle to be set must be between 3 and 20 characters
- The handle must also not be currently in use by any registered user

user\_profile\_uploadphoto():
- Store img\_url in data for each user as a uuid or None which would be default image

# Users.py
users\_all():

# Message.py
message\_send():
- A message can't be sent if it is either blank or whitespaces, an InputError will be raised


message\_remove():
- Only the user who sent the message , owner of the channel, and flockr owner can remove that message. 
- Once a message is removed, that message ID will no longer exist, however, new messages will not replace that ID. E.g. (If we have messages with ID’s of 0, 1, 2, 3, 4, and we remove ‘2’, ‘2’ will no longer exist, however, the next message will have an ID of ‘4’. 

message\_edit():
- Function cannot be called if there was no message sent originally
- Messages can be edited as either blank or whitespaces, but will remove the message if executed

message\_pin():
- Flockr owner can also pin messages not just the owner
- Flockr owner does not have to be a member in the channel to pin messages in the channel

message\_unpin():
- Flockr owner can also unpin messages not just the owner
- Flockr owner does not have to be a member in the channel to unpin messages in the channel

message\_react():
- User has to be apart of the channel to react (even if Flockr owner somehow tries to react and not apart of the channel, it won’t allow the owner to react)
- React\_id only has two states of either only being 1 or 0

message\_unreact():
- Messages can only be unreacted by the user if they have previously reacted the message
- Currently, the only react option is '1', hence, can only unreact '1'
- User needs to be part of the channel to unreact

message\_sendlater():
- Message\_id is assigned to a message at the time when it is queued up rather than when it is appended to the channel after the thread finishes running

# Admin.py
admin\_userpermission\_change():
- token, u\_id, permission\_id can't be empty values
- Flockr owners have permissions of all channel owners
- Only Flockr owners can make anyone a Flockr owner
- An owner can change a permission to the same permission
- Valid permission\_id can only be 1 (owner) or 2 (member)

# Standup.py
standup\_start():
- User has to be apart of the channel to contribute to the standup
- Time\_finish is an integer (unix timestamp)
- Only one standup can be active within a channel at the same time
- User who creates the standup has to be apart of the channel or the flockr\_owner
- Standup message gets sent using the same message\_id method as other messages in the channel
- Messages within the standup have the same message\_id method as other messages in the channel
- Standups are not deleted after being sent, and so are all kept
- Since standups are not deleted after being sent, they all have their unique standup\_id which is incremented
- Standups themselves store messages which are sent by standup\_send

standup\_active():
- Standup has only two states of either being active or inactive within a channel

standup\_send():
- Standup itself has unlimited words, however each individual standup message has max 1000 characters
- If the standup is empty by the end of the standup, then don't send any message
- Only the whole standup can be reacted and pinned, not any individual standup message within the whole standup

# Helper.py
token\_validator():
- token is jwt encoded with payload being {'u\_id': u\_id}
- validates user by checking against payload using SECRET of ‘shenpai’

token\_hash():
- SECRET is 'shenpai'
- hash token using jwt
- payload is u\_id

u\_id\_validator():
- User id can only be either valid (existing in the data) or invalid and raise an error

is\_flockr\_owner():
- user\_profile returns permission\_id
- Flockr owner has permission\_id of 1 while non flockr owners are 2

password\_hash():
- Uses hash algorithm: SHA-256
- Password is to never be unhashed

channel\_validator():
- First channel assigned channel\_id of 0, every subsequent channel created gets a channel\_id of the last channel + 1
- A channel cannot be deleted so channel\_id always remains unique
