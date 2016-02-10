#Request Functions
from Channel import MainMenu, PREFIX, TITLE
from Keyboard import Keyboard, DUMB_KEYBOARD_CLIENTS, NO_MESSAGE_CONTAINER_CLIENTS
from CouchPotato import SendToCouchpotato
from Sickbeard import SendToSickbeard
from Sonarr import SendToSonarr, ManageSonarrShow


@route(PREFIX + '/viewrequests')
def ViewRequests(query="", locked='unlocked', message=None):
    if locked == 'unlocked':
        if Client.Platform in NO_MESSAGE_CONTAINER_CLIENTS or Client.Product in NO_MESSAGE_CONTAINER_CLIENTS:
            oc = ObjectContainer(title2=message)
        else:
            oc = ObjectContainer(content=ContainerContent.Mixed, message=message)
    elif query == Prefs['password']:
        locked = 'unlocked'
        if Client.Platform in NO_MESSAGE_CONTAINER_CLIENTS or Client.Product in NO_MESSAGE_CONTAINER_CLIENTS:
            oc = ObjectContainer(title2="Password correct")
        else:
            oc = ObjectContainer(header=TITLE, message="Password is correct", content=ContainerContent.Mixed)
    else:
        return MainMenu(locked='locked', message="Password incorrect", title1="Main Menu", title2="Password incorrect")
    if not Dict['movie'] and not Dict['tv']:
        Log.Debug("There are no requests")
        if Client.Platform in NO_MESSAGE_CONTAINER_CLIENTS or Client.Product in NO_MESSAGE_CONTAINER_CLIENTS:
            oc = ObjectContainer(title1="View Requests", title2="No Requests")
        else:
            oc = ObjectContainer(header=TITLE, message="There are currently no requests.")
        oc.add(DirectoryObject(key=Callback(MainMenu, locked='unlocked'), title="Return to Main Menu", thumb=R('return.png')))
        return oc
    else:
        for movie_id in Dict['movie']:
            d = Dict['movie'][movie_id]
            title_year = d['title'] + " (" + d['year'] + ")"
            if d['automated']:
                # Log.Debug("Movie has already been sent for automation: " + title_year)
                title_year = "+ " + title_year
            if d['poster']:
                thumb = d['poster']
            else:
                thumb = R('no-poster.jpg')
            if d['summary']:
                summary = d['summary']
            else:
                summary = ""
            if d['user']:
                summary = "(Requested by " + d['user'] + ")\n " + summary
            oc.add(TVShowObject(key=Callback(ViewRequest, req_id=movie_id, req_type=d['type'], locked=locked), rating_key=movie_id, title=title_year,
                                thumb=thumb,
                                summary=summary, art=d['backdrop']))
        for series_id in Dict['tv']:
            d = Dict['tv'][series_id]
            title_year = d['title'] + " (" + d['year'] + ")"
            if d['automated']:
                # Log.Debug("Show has been sent for automation: " + title_year)
                title_year = "+ " + title_year
            if d['poster']:
                thumb = d['poster']
            else:
                thumb = R('no-poster.jpg')
            summary = ""
            if d['summary']:
                summary = d['summary']
            if d['user']:
                summary = "(Requested by " + d['user'] + ")\n " + summary
            oc.add(
                TVShowObject(key=Callback(ViewRequest, req_id=series_id, req_type=d['type'], locked=locked), rating_key=series_id, title=title_year,
                             thumb=thumb, summary=summary, art=d['backdrop']))
    oc.add(DirectoryObject(key=Callback(MainMenu, locked=locked), title="Return to Main Menu", thumb=R('return.png')))
    if len(oc) > 1 and checkAdmin():
        oc.add(DirectoryObject(key=Callback(ConfirmDeleteRequests, locked=locked), title="Clear All Requests", thumb=R('trash.png')))
    return oc


@route(PREFIX + '/getrequestspassword')
def ViewRequestsPassword(locked='locked'):
    oc = ObjectContainer(header=TITLE, message="Please enter the password in the searchbox")
    if Client.Product in DUMB_KEYBOARD_CLIENTS or Client.Platform in DUMB_KEYBOARD_CLIENTS:
        Log.Debug("Client does not support Input. Using DumbKeyboard")
        # DumbKeyboard(prefix=PREFIX, oc=oc, callback=ViewRequests, dktitle="Enter password:", dksecure=True, locked=locked)
        oc.add(DirectoryObject(key=Callback(Keyboard, callback=ViewRequests, parent=MainMenu, locked=locked), title="Enter password:"))
    else:
        oc.add(InputDirectoryObject(key=Callback(ViewRequests, locked=locked), title="Enter password:", prompt="Please enter the password:"))
    return oc


@route(PREFIX + '/confirmclearrequests')
def ConfirmDeleteRequests(locked='unlocked'):
    oc = ObjectContainer(title2="Are you sure you would like to clear all requests?")
    if Client.Platform == ClientPlatform.Android:  # If an android, add an empty first item because it gets truncated for some reason
        oc.add(DirectoryObject(key=None, title=""))
    oc.add(DirectoryObject(key=Callback(ClearRequests, locked=locked), title="Yes", thumb=R('check.png')))
    oc.add(DirectoryObject(key=Callback(ViewRequests, locked=locked), title="No", thumb=R('x-mark.png')))
    return oc


@indirect
@route(PREFIX + '/clearrequests')
def ClearRequests(locked='unlocked'):
    Dict['tv'] = {}
    Dict['movie'] = {}
    Dict.Save()
    return ViewRequests(locked=locked, message="All requests have been cleared")


@route(PREFIX + '/viewrequest')
def ViewRequest(req_id, req_type, locked='unlocked'):
    key = Dict[req_type][req_id]
    title_year = key['title'] + " (" + key['year'] + ")"
    oc = ObjectContainer(title2=title_year)
    if Client.Platform == ClientPlatform.Android:  # If an android, add an empty first item because it gets truncated for some reason
        oc.add(DirectoryObject(key=None, title=""))
    if checkAdmin():
        oc.add(DirectoryObject(key=Callback(ConfirmDeleteRequest, req_id=req_id, req_type=req_type, title_year=title_year, locked=locked),
                               title="Delete Request",
                               thumb=R('x-mark.png')))
    if key['type'] == 'movie':
        if Prefs['couchpotato_url'] and Prefs['couchpotato_api']:
            oc.add(
                DirectoryObject(key=Callback(SendToCouchpotato, movie_id=req_id, locked=locked), title="Send to CouchPotato",
                                thumb=R('couchpotato.png')))
    if key['type'] == 'tv':
        if Prefs['sonarr_url'] and Prefs['sonarr_api']:
            oc.add(DirectoryObject(key=Callback(SendToSonarr, tvdbid=req_id, locked=locked), title="Send to Sonarr", thumb=R('sonarr.png')))
        if Prefs['sickbeard_url'] and Prefs['sickbeard_api']:
            oc.add(
                DirectoryObject(key=Callback(SendToSickbeard, series_id=req_id, locked=locked), title="Send to " + Prefs['sickbeard_sickrage'], thumb=R(Prefs['sickbeard_sickrage'].lower() + '.png')))
    oc.add(DirectoryObject(key=Callback(ViewRequests, locked=locked), title="Return to View Requests", thumb=R('return.png')))
    return oc


@route(PREFIX + '/confirmdeleterequest')
def ConfirmDeleteRequest(req_id, req_type, title_year="", locked='unlocked'):
    oc = ObjectContainer(title2="Are you sure you would like to delete the request for " + title_year + "?")
    if Client.Platform == ClientPlatform.Android:  # If an android, add an empty first item because it gets truncated for some reason
        oc.add(DirectoryObject(key=None, title=""))
    oc.add(DirectoryObject(key=Callback(DeleteRequest, req_id=req_id, req_type=req_type, locked=locked), title="Yes", thumb=R('check.png')))
    oc.add(DirectoryObject(key=Callback(ViewRequest, req_id=req_id, req_type=req_type, locked=locked), title="No", thumb=R('x-mark.png')))
    return oc


@indirect
@route(PREFIX + '/deleterequest')
def DeleteRequest(req_id, req_type, locked='unlocked'):
    if req_id in Dict[req_type]:
        message = "Request was deleted"
        del Dict[req_type][req_id]
        Dict.Save()
    else:
        message = "Request could not be deleted"
    return ViewRequests(locked=locked, message=message)