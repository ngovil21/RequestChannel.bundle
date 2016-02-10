# Main Channel Methods

TITLE = 'Plex Request Channel'
PREFIX = '/video/plexrequestchannel'


### Notification Constants ############################
PUSHBULLET_API_URL = "https://api.pushbullet.com/v2/"
PUSHOVER_API_URL = "https://api.pushover.net/1/messages.json"
PUSHOVER_API_KEY = "ajMtuYCg8KmRQCNZK2ggqaqiBw2UHi"


#######################################################


@route(PREFIX + '/mainmenu')
def CMainMenu(locked='locked', message=None, title1=TITLE, title2="Main Menu"):
    Log.Debug("Platform: " + str(Client.Platform))
    Log.Debug("Product: " + str(Client.Product))
    if Client.Platform in NO_MESSAGE_CONTAINER_CLIENTS or Client.Product in NO_MESSAGE_CONTAINER_CLIENTS:
        oc = ObjectContainer(replace_parent=True, title1=title1, title2=title2)
    else:
        oc = ObjectContainer(replace_parent=True, message=message, title1=title1, title2=title2)
    is_admin = checkAdmin()
    if is_admin:
        Log.Debug("User is Admin")
    token = Request.Headers['X-Plex-Token']
    if is_admin and token in Dict['register']:  # Do not save admin token in the register
        del Dict['register'][token]
    if Prefs['register'] and not is_admin and (token not in Dict['register'] or not Dict['register'][token]['nickname']):
        return Register(locked=locked)
    if not is_admin and token not in Dict['register']:
        Dict['register'][token] = {'nickname': "", 'requests': 0}
    register_date = Datetime.FromTimestamp(Dict['register_reset'])
    if (register_date + Datetime.Delta(days=7)) < Datetime.Now():
        resetRegister()
    if Client.Product in DUMB_KEYBOARD_CLIENTS or Client.Platform in DUMB_KEYBOARD_CLIENTS:  # Clients in this list do not support InputDirectoryObjects
        Log.Debug("Client does not support Input. Using DumbKeyboard")
        oc.add(DirectoryObject(
            key=Callback(Keyboard, callback=Movie.SearchMovie, parent=CMainMenu, locked=locked, title="Search for Movie",
                         message="Enter the name of the movie"),
            title="Request a Movie"))
        oc.add(DirectoryObject(
            key=Callback(Keyboard, callback=TVShow.SearchTV, parent=CMainMenu, locked=locked, title="Search for TV Show",
                         message="Enter the name of the TV Show"),
            title="Request a TV Show"))
    elif Client.Product == "Plex Web":  # Plex Web does not create a popup input directory object, so use an intermediate menu
        oc.add(DirectoryObject(key=Callback(Movie.AddNewMovie, title="Request a Movie", locked=locked), title="Request a Movie"))
        oc.add(DirectoryObject(key=Callback(TVShow.AddNewTVShow, locked=locked), title="Request a TV Show"))
    else:  # All other clients
        oc.add(
            InputDirectoryObject(key=Callback(Movie.SearchMovie, locked=locked), title="Search for Movie", prompt="Enter the name of the movie:"))
        oc.add(
            InputDirectoryObject(key=Callback(TVShow.SearchTV, locked=locked), title="Search for TV Show", prompt="Enter the name of the TV Show:"))
    if Prefs['usersviewrequests'] or is_admin:
        if locked == 'unlocked' or Prefs['password'] is None or Prefs['password'] == "":
            oc.add(DirectoryObject(key=Callback(Requests.ViewRequests, locked='unlocked'), title="View Requests"))  # No password needed this session
        else:
            oc.add(DirectoryObject(key=Callback(Requests.ViewRequestsPassword, locked='locked'),
                                   title="View Requests"))  # Set View Requests to locked and ask for password
    if is_admin:
        if Prefs['sonarr_api']:
            oc.add(DirectoryObject(key=Callback(Sonarr.ManageSonarr, locked=locked), title="Manage Sonarr"))
        oc.add(DirectoryObject(key=Callback(ManageChannel.ManageChannel, locked=locked), title="Manage Channel"))
    elif not Dict['register'][token]['nickname']:
        oc.add(DirectoryObject(
            key=Callback(Register, message="Entering your name will let the admin know who you are when making requests.", locked=locked),
            title="Register Device"))

    return oc


def resetRegister():
    for key in Dict['register']:
        Dict['register'][key]['requests'] = 0
    Dict['register_reset'] = Datetime.TimestampFromDatetime(Datetime.Now())


@route(PREFIX + '/register')
def Register(message="Unrecognized device. The admin would like you to register it.", locked='locked'):
    if Client.Product == "Plex Web":
        message += "\nEnter your name in the searchbox and press enter."
    if Client.Platform in NO_MESSAGE_CONTAINER_CLIENTS or Client.Product in NO_MESSAGE_CONTAINER_CLIENTS:
        oc = ObjectContainer(title1="Unrecognized Device", title2="Please register")
    else:
        oc = ObjectContainer(header=TITLE, message=message)
    if Client.Product in DUMB_KEYBOARD_CLIENTS or Client.Platform in DUMB_KEYBOARD_CLIENTS:
        Log.Debug("Client does not support Input. Using DumbKeyboard")
        # DumbKeyboard(prefix=PREFIX, oc=oc, callback=RegisterName, dktitle="Enter your name or nickname", locked=locked)
        oc.add(DirectoryObject(key=Callback(Keyboard, callback=RegisterName, parent=CMainMenu, locked=locked), title="Enter your name or nickname"))
    else:
        oc.add(InputDirectoryObject(key=Callback(RegisterName, locked=locked), title="Enter your name or nickname",
                                    prompt="Enter your name or nickname"))
    return oc


@route(PREFIX + '/registername')
def RegisterName(query="", locked='locked'):
    if not query:
        return Register(message="You must enter a name. Try again.", locked=locked)
    token = Request.Headers['X-Plex-Token']
    Dict['register'][token] = {'nickname': query, 'requests': 0}
    return CMainMenu(message="Your device has been registered. Thank you.", locked=locked, title1="Main Menu", title2="Registered")


def checkAdmin():
    import urllib2
    try:
        token = Request.Headers['X-Plex-Token']
        req = urllib2.Request("http://127.0.0.1:32400/myplex/account", headers={'X-Plex-Token': token})
        resp = urllib2.urlopen(req)
        if resp.read():
            return True
    except:
        pass
    return False
