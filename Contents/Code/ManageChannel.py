#ManageChannel Functions
import Channel
from Keyboard import Keyboard, DUMB_KEYBOARD_CLIENTS, NO_MESSAGE_CONTAINER_CLIENTS

@route(Channel.PREFIX + "/managechannel")
def ManageChannel(message=None, title1=Channel.TITLE, title2="Manage Channel", locked='locked'):
    if not checkAdmin():
        return Channel.CMainMenu("Only an admin can manage the channel!", locked=locked, title1="Main Menu", title2="Admin only")
    if Client.Platform in NO_MESSAGE_CONTAINER_CLIENTS or Client.Product in NO_MESSAGE_CONTAINER_CLIENTS:
        oc = ObjectContainer(title1="Manage", title2=message)
    else:
        oc = ObjectContainer(header=Channel.TITLE, message=message)
    oc.add(DirectoryObject(key=Callback(ManageUsers, locked=locked), title="Manage Users"))
    oc.add(PopupDirectoryObject(key=Callback(ResetDict, locked=locked), title="Reset Dictionary Settings"))
    oc.add(DirectoryObject(key=Callback(Channel.CMainMenu, locked=locked), title="Return to Main Menu"))
    return oc


@route(Channel.PREFIX + "/manageusers")
def ManageUsers(locked='locked', message=None):
    if not checkAdmin():
        return Channel.CMainMenu("Only an admin can manage the channel!", locked=locked, title1="Main Menu", title2="Admin only")
    if Client.Platform in NO_MESSAGE_CONTAINER_CLIENTS or Client.Product in NO_MESSAGE_CONTAINER_CLIENTS:
        oc = ObjectContainer(title1="Manage Users", title2=message)
    else:
        oc = ObjectContainer(header=Channel.TITLE, message=message)
    if len(Dict['register']) > 0:
        for token in Dict['register']:
            if 'nickname' in Dict['register'][token] and Dict['register'][token]['nickname']:
                user = Dict['register'][token]['nickname']
            else:
                user = "User " + Hash.SHA1(token)[:10]  # Get first 10 digits of token hash to try to identify user.
            oc.add(
                DirectoryObject(key=Callback(ManageUser, token=token, locked=locked), title=user + ": " + str(Dict['register'][token]['requests'])))
    oc.add(DirectoryObject(key=Callback(ManageChannel, locked=locked), title="Return to Manage Channel"))
    return oc


@route(Channel.PREFIX + "/manageuser")
def ManageUser(token, locked='locked', message=None):
    if not checkAdmin():
        return Channel.CMainMenu("Only an admin can manage the channel!", locked=locked, title1="Main Menu", title2="Admin only")
    if 'nickname' in Dict['register'][token] and Dict['register'][token]['nickname']:
        user = Dict['register'][token]['nickname']
    else:
        user = "User " + Hash.SHA1(token)[:10]  # Get first 10 digits of token hash to try to identify user.
    if Client.Platform in NO_MESSAGE_CONTAINER_CLIENTS or Client.Product in NO_MESSAGE_CONTAINER_CLIENTS:
        oc = ObjectContainer(title1="Manage User", title2=message)
    else:
        oc = ObjectContainer(title1="Manage User", title2=user, message=message)
    oc.add(DirectoryObject(key=Callback(ManageUser, token=token, locked=locked),
                           title=user + " has made " + str(Dict['register'][token]['requests']) + " requests."))
    if token in Dict['blocked']:
        oc.add(DirectoryObject(key=Callback(BlockUser, token=token, set='False', locked=locked), title="Unblock User"))
    else:
        oc.add(DirectoryObject(key=Callback(BlockUser, token=token, set='True', locked=locked), title="Block User"))
    oc.add(PopupDirectoryObject(key=Callback(DeleteUser, token=token, locked=locked, confirmed='False'), title="Delete User"))
    oc.add(DirectoryObject(key=Callback(ManageChannel, locked=locked), title="Return to Manage Channel"))

    return oc


@route(Channel.PREFIX + "/blockuser")
def BlockUser(token, set, locked='locked'):
    if set == 'True':
        if token in Dict['blocked']:
            return ManageUser(token=token, locked=locked, message="User is already blocked.")
        else:
            Dict['blocked'].append(token)
            return ManageUser(token=token, locked=locked, message="User has been blocked.")
    elif set == 'False':
        if token in Dict['blocked']:
            Dict['blocked'].remove(token)
            return ManageUser(token=token, locked=locked, message="User has been unblocked.")
    return ManageUser(token=token, locked=locked)


@route(Channel.PREFIX + "/deleteuser")
def DeleteUser(token, locked='locked', confirmed='False'):
    if not checkAdmin():
        return Channel.CMainMenu("Only an admin can manage the channel!", locked=locked, title1="Main Menu", title2="Admin only")
    oc = ObjectContainer(title1="Confirm Delete User?", title2=Dict['register'][token]['nickname'])
    if confirmed == 'False':
        oc.add(DirectoryObject(key=Callback(DeleteUser, token=token, locked=locked, confirmed='True'), title="Yes"))
        oc.add(DirectoryObject(key=Callback(ManageUser, token=token, locked=locked), title="No"))
    elif confirmed == 'True':
        del Dict['register'][token]
        return ManageUser(locked=locked, message="User registration has been deleted.")
    return oc


@route(Channel.PREFIX + "/resetdict")
def ResetDict(locked='locked', confirm='False'):
    if not checkAdmin():
        return Channel.CMainMenu("Only an admin can manage the channel!", title1="Main Menu", title2="Admin only")
    if confirm == 'False':
        if Client.Platform in NO_MESSAGE_CONTAINER_CLIENTS or Client.Product in NO_MESSAGE_CONTAINER_CLIENTS:
            oc = ObjectContainer(title1="Reset Info", title2="Confirm")
        else:
            oc = ObjectContainer(header=Channel.TITLE,
                                 message="Are you sure you would like to clear all saved info? This will clear all requests and user information.")
        oc.add(DirectoryObject(key=Callback(ResetDict, locked=locked, confirm='True'), title="Yes"))
        oc.add(DirectoryObject(key=Callback(ManageChannel, locked=locked), title="No"))
        return oc
    elif confirm == 'True':
        Dict.Reset()
        Dict['tv'] = {}
        Dict['movie'] = {}
        Dict['register'] = {}
        Dict['register_reset'] = Datetime.TimestampFromDatetime(Datetime.Now())
        Dict['blocked'] = []

    return ManageChannel(message="Dictionary has been reset!", locked=locked)