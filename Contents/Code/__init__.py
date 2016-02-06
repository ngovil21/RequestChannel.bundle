from DumbTools import DumbKeyboard

TITLE = 'Plex Request Channel'
PREFIX = '/video/plexrequestchannel'

ART = 'art-default.jpg'
ICON = 'plexrequestchannel.png'

DATA_FILE = "Requests"

MOVIE_DB = "OpenMovieDatabase"

### URL Constants for TheMovieDataBase ##################
TMDB_API_KEY = "096c49df1d0974ee573f0295acb9e3ce"
TMDB_API_URL = "http://api.themoviedb.org/3/"
TMDB_IMAGE_BASE_URL = "http://image.tmdb.org/t/p/"
POSTER_SIZE = "w500/"
BACKDROP_SIZE = "original/"
########################################################

### URL Constants for OpenMovieDataBase ################
OMDB_API_URL = "http://www.omdbapi.com/"
########################################################

### URL Constants for TheTVDB ##########################
TVDB_API_KEY = "B93EF22D769A70CB"
TVDB_API_URL = "http://thetvdb.com/api/"
TVDB_BANNER_URL = "http://thetvdb.com/banners/"
#######################################################

### Notification Constants ############################
PUSHBULLET_API_URL = "https://api.pushbullet.com/v2/"
PUSHOVER_API_URL = "https://api.pushover.net/1/messages.json"
PUSHOVER_API_KEY = "ajMtuYCg8KmRQCNZK2ggqaqiBw2UHi"

DUMB_KEYBOARD_CLIENTS = ['Plex for iOS', 'Plex Media Player', 'Plex Home Theater', 'OpenPHT', 'Plex for Roku', 'iOS', 'Roku', 'tvOS' 'Konvergo']


########################################################
#   Start Code
########################################################

def Start():
    ObjectContainer.title1 = TITLE
    ObjectContainer.art = R(ART)

    DirectoryObject.thumb = R(ICON)
    DirectoryObject.art = R(ART)
    EpisodeObject.thumb = R(ICON)
    EpisodeObject.art = R(ART)
    VideoClipObject.thumb = R(ICON)
    VideoClipObject.art = R(ART)

    Plugin.AddViewGroup("Details", viewMode="InfoList", mediaType="items")

    if not 'tv' in Dict:
        Dict['tv'] = {}
    if not 'movie' in Dict:
        Dict['movie'] = {}
    if not 'register' in Dict:
        Dict['register'] = {}
        Dict['register_reset'] = Datetime.TimestampFromDatetime(Datetime.Now())
    Dict.Save()


###################################################################################################
# This tells Plex how to list you in the available channels and what type of channels this is
@handler(PREFIX, TITLE, art=ART, thumb=ICON)
@route(PREFIX + '/mainmenu')
def MainMenu(locked='locked', message=None):
    Log.Debug("Platform: " + str(Client.Platform))
    Log.Debug("Product: " + str(Client.Product))
    oc = ObjectContainer(replace_parent=True, message=message)
    is_admin = checkAdmin()
    if is_admin:
        Log.Debug("User is Admin")
    token = Request.Headers['X-Plex-Token']
    if is_admin and token in Dict['register']:  # Do not save admin token in the register
        del Dict['register'][token]
    if not is_admin and Dict['register'] and (token not in Dict['register'] or not Dict['register'][token]['nickname']):
        return Register(locked=locked)
    if not is_admin and token not in Dict['register']:
        Dict['register'][token] = {'nickname': "", 'requests': 0}
    register_date = Datetime.FromTimestamp(Dict['register_reset'])
    if (register_date + Datetime.Delta(days=7)) < Datetime.Now():
        resetRegister()
    oc.add(DirectoryObject(key=Callback(AddNewMovie, title="Request a Movie", locked=locked), title="Request a Movie"))
    oc.add(DirectoryObject(key=Callback(AddNewTVShow, title="Request a TV Show", locked=locked), title="Request a TV Show"))
    if Prefs['usersviewrequests'] or is_admin:
        if locked == 'unlocked' or Prefs['password'] is None or Prefs['password'] == "":
            oc.add(DirectoryObject(key=Callback(ViewRequests, locked='unlocked'), title="View Requests"))  # No password needed this session
        else:
            oc.add(DirectoryObject(key=Callback(ViewRequestsPassword, locked='locked'),
                                   title="View Requests"))  # Set View Requests to locked and ask for password
    if is_admin:
        oc.add(DirectoryObject(key=Callback(ManageChannel, locked=locked), title="Manage Channel"))

    return oc


def resetRegister():
    for key in Dict['register']:
        Dict['register'][key]['requests'] = 0
    Dict['register_reset'] = Datetime.TimestampFromDatetime(Datetime.Now())


@route(PREFIX + '/register')
def Register(message="Unrecognized device. The admin would like you to register it.", locked='locked'):
    if Client.Product == "Plex Web":
        message += "\nEnter your name in the searchbox and press enter."
    oc = ObjectContainer(header=TITLE, message=message)
    if Client.Product in DUMB_KEYBOARD_CLIENTS or Client.Platform in DUMB_KEYBOARD_CLIENTS:
        Log.Debug("Client does not support Input. Using DumbKeyboard")
        DumbKeyboard(prefix=PREFIX, oc=oc, callback=RegisterName, dktitle="Enter your name or nickname", locked=locked)
    else:
        oc.add(InputDirectoryObject(key=Callback(RegisterName, locked=locked), title="Enter your name or nickname",
                                    prompt="Enter your name or nickname"))
    return oc


@indirect
@route(PREFIX + '/registername')
def RegisterName(query="", locked='locked'):
    if not query:
        return Register(message="You must enter a name. Try again.", locked=locked)
    token = Request.Headers['X-Plex-Token']
    Dict['register'][token] = {'nickname': query, 'requests': 0}
    return MainMenu(message="Your device has been registered. Thank you.", locked=locked)


@route(PREFIX + '/addnewmovie')
def AddNewMovie(title="Request a Movie", locked='unlocked'):
    if Prefs['weekly_limit'] and int(Prefs['weekly_limit']) > 0 and not checkAdmin():
        token = Request.Headers['X-Plex-Token']
        if Dict['register'].get(token, None) and Dict['register'][token]['requests'] >= int(Prefs['weekly_limit']):
            return MainMenu(message="Sorry you have reached your weekly request limit of " + Prefs['weekly_limit'] + ".", locked=locked)
    oc = ObjectContainer(header=TITLE, message="Please enter the movie name in the searchbox and press enter.")
    if Client.Product in DUMB_KEYBOARD_CLIENTS:
        Log.Debug("Client does not support Input. Using DumbKeyboard")
        DumbKeyboard(prefix=PREFIX, oc=oc, callback=SearchMovie, dktitle=title, dkthumb=R('search.png'), locked=locked)
    else:
        oc.add(
            InputDirectoryObject(key=Callback(SearchMovie, locked=locked), title=title, prompt="Enter the name of the movie:", thumb=R('search.png')))
    return oc


@route(PREFIX + '/searchmovie')
def SearchMovie(title="Search Results", query="", locked='unlocked'):
    oc = ObjectContainer(title1=title, content=ContainerContent.Movies, view_group="Details")
    query = String.Quote(query, usePlus=True)
    if Prefs['movie_db'] == "TheMovieDatabase":
        headers = {
            'Accept': 'application/json'
        }
        request = JSON.ObjectFromURL(url=TMDB_API_URL + "search/movie?api_key=" + TMDB_API_KEY + "&query=" + query, headers=headers)
        if 'results' in request:
            results = request['results']
            for key in results:
                if not key['title']:
                    continue
                if key['release_date']:
                    year = key['release_date'][0:4]
                else:
                    year = ""
                if key['poster_path']:
                    thumb = TMDB_IMAGE_BASE_URL + POSTER_SIZE + key['poster_path']
                else:
                    thumb = None
                if key['backdrop_path']:
                    art = TMDB_IMAGE_BASE_URL + BACKDROP_SIZE + key['backdrop_path']
                else:
                    art = None
                title_year = key['title'] + " (" + year + ")"
                oc.add(DirectoryObject(
                    key=Callback(ConfirmMovieRequest, id=key['id'], source='tmdb', title=key['title'], year=year, poster=thumb, backdrop=art,
                                 summary=key['overview'], locked=locked), title=title_year, thumb=thumb, summary=key['overview'], art=art))
        else:
            Log.Debug("No Results Found")
            if Client.Product in DUMB_KEYBOARD_CLIENTS or Client.Platform in DUMB_KEYBOARD_CLIENTS:
                Log.Debug("Client does not support Input. Using DumbKeyboard")
                DumbKeyboard(prefix=PREFIX, oc=oc, callback=SearchMovie, dktitle="Search Again", dkthumb=R('search.png'), locked=locked)
            else:
                oc.add(InputDirectoryObject(key=Callback(SearchMovie, locked=locked), title="Search Again",
                                            prompt="Enter the name of the movie:"))
            oc = ObjectContainer(header=TITLE, message="Sorry there were no results found for your search.")
            oc.add(DirectoryObject(key=Callback(MainMenu, locked=locked), title="Back to Main Menu", thumb=R('return.png')))
            return oc
    else:  # Use OMDB By Default
        request = JSON.ObjectFromURL(url=OMDB_API_URL + "?s=" + query + "&r=json")
        if 'Search' in request:
            results = request['Search']
            for key in results:
                if not key['Title']:
                    continue
                if 'type' in key and not (key['type'] == "movie"):  # only show movie results
                    continue
                title_year = key['Title'] + " (" + key['Year'] + ")"
                if key['Poster']:
                    thumb = key['Poster']
                else:
                    thumb = R('no-poster.jpg')
                oc.add(TVShowObject(
                    key=Callback(ConfirmMovieRequest, id=key['imdbID'], source='imdb', title=key['Title'], year=key['Year'], poster=key['Poster'],
                                 locked=locked), rating_key=key['imdbID'], title=title_year, thumb=thumb))
        else:
            Log.Debug("No Results Found")
            oc = ObjectContainer(header=TITLE, message="Sorry there were no results found for your search.")
            if Client.Product in DUMB_KEYBOARD_CLIENTS or Client.Platform in DUMB_KEYBOARD_CLIENTS:
                Log.Debug("Client does not support Input. Using DumbKeyboard")
                DumbKeyboard(prefix=PREFIX, oc=oc, callback=SearchMovie, dktitle="Search Again", dkthumb=R('search.png'), locked=locked)
            else:
                oc.add(InputDirectoryObject(key=Callback(SearchMovie, locked=locked), title="Search Again",
                                            prompt="Enter the name of the movie:"))
            oc.add(DirectoryObject(key=Callback(MainMenu, locked=locked), title="Back to Main Menu", thumb=R('return.png')))
            return oc
    if Client.Product in DUMB_KEYBOARD_CLIENTS or Client.Platform in DUMB_KEYBOARD_CLIENTS:
        Log.Debug("Client does not support Input. Using DumbKeyboard")
        DumbKeyboard(prefix=PREFIX, oc=oc, callback=SearchMovie, dktitle="Search Again", dkthumb=R('search.png'), locked=locked)
    else:
        oc.add(InputDirectoryObject(key=Callback(SearchMovie, locked=locked), title="Search Again",
                                    prompt="Enter the name of the movie:", thumb=R('search.png')))
    oc.add(DirectoryObject(key=Callback(MainMenu, locked=locked), title="Return to Main Menu", thumb=R('return.png')))
    return oc


@route(PREFIX + '/confirmmovierequest')
def ConfirmMovieRequest(id, title, source='', year="", poster="", backdrop="", summary="", locked='unlocked'):
    title_year = title + " " + "(" + year + ")"
    oc = ObjectContainer(title1="Confirm Movie Request", title2="Are you sure you would like to request the movie " + title_year + "?")

    if Client.Platform == ClientPlatform.Android:  # If an android, add an empty first item because it gets truncated for some reason
        oc.add(DirectoryObject(key=None, title=""))
    oc.add(DirectoryObject(
        key=Callback(AddMovieRequest, id=id, source=source, title=title, year=year, poster=poster, backdrop=backdrop, summary=summary, locked=locked),
        title="Yes", thumb=R('check.png')))
    oc.add(DirectoryObject(key=Callback(MainMenu, locked=locked), title="No", thumb=R('x-mark.png')))

    return oc


@indirect
@route(PREFIX + '/addmovierequest')
def AddMovieRequest(id, title, source='', year="", poster="", backdrop="", summary="", locked='unlocked'):
    if id in Dict['movie']:
        Log.Debug("Movie is already requested")
        oc = ObjectContainer(header=TITLE, message="Movie has already been requested.")
        oc.add(DirectoryObject(key=Callback(MainMenu, locked=locked), title="Return to Main Menu", thumb=R('return.png')))
        return MainMenu(locked=locked, message="Movie has already been requested")
    else:
        user = ""
        token = Request.Headers['X-Plex-Token']
        if token in Dict['register'] and Dict['register'][token]['nickname']:
            user = Dict['register'][token]['nickname']
            Dict['register'][token]['requests'] = Dict['register'][token]['requests'] + 1
        title_year = title + " (" + year + ")"
        Dict['movie'][id] = {'type': 'movie', 'id': id, 'source': source, 'title': title, 'year': year, 'title_year': title_year, 'poster': poster,
                             'backdrop': backdrop, 'summary': summary, 'user': user, 'automated': False}
        Dict.Save()
        if Prefs['couchpotato_autorequest']:
            SendToCouchpotato(id)
        notifyRequest(id=id, type='movie')
        oc = ObjectContainer(header=TITLE, message="Movie has been requested.")
        oc.add(DirectoryObject(key=Callback(MainMenu, locked=locked), title="Return to Main Menu", thumb=R('return.png')))
        return MainMenu(locked=locked, message="Movie has been requested")


@route(PREFIX + '/addtvshow')
def AddNewTVShow(title="", locked='unlocked'):
    if Prefs['weekly_limit'] and int(Prefs['weekly_limit'] > 0) and not checkAdmin():
        token = Request.Headers['X-Plex-Token']
        if token in Dict['register'] and Dict['register'][token]['requests'] >= int(Prefs['weekly_limit']):
            return MainMenu(message="Sorry you have reached your weekly request limit of " + Prefs['weekly_limit'] + ".", locked=locked)
    oc = ObjectContainer(header=TITLE, message="Please enter the name of the TV Show in the searchbox and press enter.")
    if Client.Product in DUMB_KEYBOARD_CLIENTS or Client.Platform in DUMB_KEYBOARD_CLIENTS:
        Log.Debug("Client does not support Input. Using DumbKeyboard")
        DumbKeyboard(prefix=PREFIX, oc=oc, callback=SearchTV, dktitle="Request a TV Show", dkthumb=R('search.png'), locked=locked)
    else:
        oc.add(InputDirectoryObject(key=Callback(SearchTV, locked=locked), title="Request a TV Show", prompt="Enter the name of the TV Show:",
                                    thumb=R('search.png')))
    return oc


@route(PREFIX + '/searchtv')
def SearchTV(query, locked='unlocked'):
    oc = ObjectContainer(title1="Search Results", content=ContainerContent.Shows, view_group="Details")
    query = String.Quote(query, usePlus=True)
    xml = XML.ElementFromURL(TVDB_API_URL + "GetSeries.php?seriesname=" + query)
    series = xml.xpath("//Series")
    if len(series) == 0:
        oc = ObjectContainer(header=TITLE, message="Sorry there were no results found.")
        if Client.Product in DUMB_KEYBOARD_CLIENTS or Client.Platform in DUMB_KEYBOARD_CLIENTS:
            Log.Debug("Client does not support Input. Using DumbKeyboard")
            DumbKeyboard(prefix=PREFIX, oc=oc, callback=SearchTV, dktitle="Search Again", dkthumb=R('search.png'), locked=locked)
        else:
            oc.add(InputDirectoryObject(key=Callback(SearchTV, locked=locked), title="Search Again", prompt="Enter the name of the TV Show:",
                                        thumb=R('search.png')))
        oc.add(DirectoryObject(key=Callback(MainMenu, locked=locked), title="Return to Main Menu", thumb=R('return.png')))
        return oc
    count = 0
    for serie in series:
        id = ""
        title = ""
        year = ""
        poster = ""
        summary = ""
        for child in serie.getchildren():
            if child.tag.lower() == "seriesid" and child.text:
                id = child.text
            elif child.tag.lower() == "seriesname" and child.text:
                title = child.text
            elif child.tag.lower() == "banner" and child.text and not poster:
                poster = TVDB_BANNER_URL + child.text
            elif child.tag.lower() == "overview" and child.text:
                summary = child.text
            elif child.tag.lower() == "firstaired" and child.text:
                release_date = child.text
                year = release_date[0:4]
            elif child.tag.lower() == "poster" and child.text:
                poster = TVDB_BANNER_URL + child.text
        if count < 11:  # Let's look for the actual poster for only the first 10 tv shows to reduce api hits
            try:
                serie_page = XML.ElementFromURL(TVDB_API_URL + TVDB_API_KEY + "/series/" + id)
                poster_text = serie_page.xpath("//Series/poster/text()")
                if poster_text:
                    poster = TVDB_BANNER_URL + poster_text[0]
            except Exception as e:
                Log.Debug(e)
            count += 1
        if id == "":
            Log.Debug("No id found!")
        if year:
            title_year = title + " (" + year + ")"
        else:
            title_year = title
        if poster:
            thumb = poster
        else:
            thumb = R('no-poster.jpg')
        oc.add(
            TVShowObject(key=Callback(ConfirmTVRequest, id=id, source='tvdb', title=title, year=year, poster=poster, summary=summary, locked=locked),
                         rating_key=id, title=title_year, summary=summary, thumb=thumb))
    if Client.Product in DUMB_KEYBOARD_CLIENTS or Client.Platform in DUMB_KEYBOARD_CLIENTS:
        Log.Debug("Client does not support Input. Using DumbKeyboard")
        DumbKeyboard(prefix=PREFIX, oc=oc, callback=SearchTV, dktitle="Search Again", dkthumb=R('search.png'), locked=locked)
    else:
        oc.add(InputDirectoryObject(key=Callback(SearchTV, locked=locked), title="Search Again", prompt="Enter the name of the TV Show:",
                                    thumb=R('search.png')))
    oc.add(DirectoryObject(key=Callback(MainMenu, locked=locked), title="Return to Main Menu", thumb=R('return.png')))
    return oc


@route(PREFIX + '/confirmtvrequest')
def ConfirmTVRequest(id, title, source="", year="", poster="", backdrop="", summary="", locked='unlocked'):
    if year:
        title_year = title + " " + "(" + year + ")"
    else:
        title_year = title
    oc = ObjectContainer(title1="Confirm TV Request", title2="Are you sure you would like to request the TV Show " + title_year + "?")

    if Client.Platform == ClientPlatform.Android:  # If an android, add an empty first item because it gets truncated for some reason
        oc.add(DirectoryObject(key=None, title=""))
    oc.add(DirectoryObject(
        key=Callback(AddTVRequest, id=id, source=source, title=title, year=year, poster=poster, backdrop=backdrop, summary=summary, locked=locked),
        title="Yes", thumb=R('check.png')))
    oc.add(DirectoryObject(key=Callback(MainMenu, locked=locked), title="No", thumb=R('x-mark.png')))

    return oc


@indirect
@route(PREFIX + '/addtvrequest')
def AddTVRequest(id, title, source='', year="", poster="", backdrop="", summary="", locked='unlocked'):
    if id in Dict['tv']:
        Log.Debug("TV Show is already requested")
        return MainMenu(locked=locked, message="TV Show has already been requested")
    else:
        token = Request.Headers['X-Plex-Token']
        user = ""
        if token in Dict['register'] and Dict['register'][token]['nickname']:
            user = Dict['register'][token]['nickname']
            Dict['register'][token]['requests'] = Dict['register'][token]['requests'] + 1
        Dict['tv'][id] = {'type': 'tv', 'id': id, 'source': source, 'title': title, 'year': year, 'poster': poster, 'backdrop': backdrop,
                          'summary': summary, 'user': user, 'automated': False}
        Dict.Save()
        if Prefs['sonarr_autorequest'] and Prefs['sonarr_url'] and Prefs['sonarr_api']:
            SendToSonarr(id)
        if Prefs['sickrage_autorequest'] and Prefs['sickrage_url'] and Prefs['sickrage_api']:
            SendToSickrage(id)
        notifyRequest(id=id, type='tv')
        oc = ObjectContainer(header=TITLE, message="TV Show has been requested.")
        oc.add(DirectoryObject(key=Callback(MainMenu, locked=locked), title="Return to Main Menu", thumb=R('return.png')))

        return MainMenu(locked=locked, message="TV Show has been requested")


@route(PREFIX + '/viewrequests')
def ViewRequests(query="", locked='unlocked', message=None):
    if locked == 'unlocked':
        oc = ObjectContainer(content=ContainerContent.Mixed, message=message)
    elif query == Prefs['password']:
        locked = 'unlocked'
        oc = ObjectContainer(header=TITLE, message="Password is correct", content=ContainerContent.Mixed)
    else:
        oc = ObjectContainer(header=TITLE, message="Password is incorrect!")
        oc.add(DirectoryObject(key=Callback(MainMenu, locked=locked), title="Return to Main Menu"))
        return oc
    if not Dict['movie'] and not Dict['tv']:
        Log.Debug("There are no requests")
        oc = ObjectContainer(header=TITLE, message="There are currently no requests.")
        oc.add(DirectoryObject(key=Callback(MainMenu, locked='unlocked'), title="Return to Main Menu", thumb=R('return.png')))
        return oc
    else:
        for id in Dict['movie']:
            d = Dict['movie'][id]
            title_year = d['title'] + " (" + d['year'] + ")"
            if d['automated']:
                Log.Debug("Movie has already been sent for automation: " + title_year)
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
            oc.add(TVShowObject(key=Callback(ViewRequest, id=id, type=d['type'], locked=locked), rating_key=id, title=title_year, thumb=thumb,
                                summary=summary, art=d['backdrop']))
        for id in Dict['tv']:
            d = Dict['tv'][id]
            title_year = d['title'] + " (" + d['year'] + ")"
            if d['automated']:
                Log.Debug("Show has been sent for automation: " + title_year)
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
                TVShowObject(key=Callback(ViewRequest, id=id, type=d['type'], locked=locked), rating_key=id, title=title_year, thumb=thumb,
                             summary=summary, art=d['backdrop']))
    oc.add(DirectoryObject(key=Callback(MainMenu, locked=locked), title="Return to Main Menu", thumb=R('return.png')))
    if len(oc) > 1 and checkAdmin():
        oc.add(DirectoryObject(key=Callback(ConfirmDeleteRequests, locked=locked), title="Clear All Requests", thumb=R('trash.png')))
    return oc


@route(PREFIX + '/getrequestspassword')
def ViewRequestsPassword(locked='locked'):
    oc = ObjectContainer(header=TITLE, message="Please enter the password in the searchbox")
    if Client.Product in DUMB_KEYBOARD_CLIENTS or Client.Platform in DUMB_KEYBOARD_CLIENTS:
        Log.Debug("Client does not support Input. Using DumbKeyboard")
        DumbKeyboard(prefix=PREFIX, oc=oc, callback=ViewRequests, dktitle="Enter password:", dksecure=True, locked=locked)
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
def ViewRequest(id, type, locked='unlocked'):
    key = Dict[type][id]
    title_year = key['title'] + " (" + key['year'] + ")"
    oc = ObjectContainer(title2=title_year)
    if Client.Platform == ClientPlatform.Android:  # If an android, add an empty first item because it gets truncated for some reason
        oc.add(DirectoryObject(key=None, title=""))
    if checkAdmin():
        oc.add(DirectoryObject(key=Callback(ConfirmDeleteRequest, id=id, type=type, title_year=title_year, locked=locked), title="Delete Request",
                               thumb=R('x-mark.png')))
    if key['type'] == 'movie':
        if Prefs['couchpotato_url'] and Prefs['couchpotato_api']:
            oc.add(DirectoryObject(key=Callback(SendToCouchpotato, id=id, locked=locked), title="Send to CouchPotato", thumb=R('couchpotato.png')))
    if key['type'] == 'tv':
        if Prefs['sonarr_url'] and Prefs['sonarr_api']:
            oc.add(DirectoryObject(key=Callback(SendToSonarr, id=id, locked=locked), title="Send to Sonarr", thumb=R('sonarr.png')))
        if Prefs['sickrage_url'] and Prefs['sickrage_api']:
            oc.add(DirectoryObject(key=Callback(SendToSickrage, id=id, locked=locked), title="Send to Sickrage", thumb=R('sickrage.png')))
    oc.add(DirectoryObject(key=Callback(ViewRequests, locked=locked), title="Return to View Requests", thumb=R('return.png')))
    return oc


@route(PREFIX + '/confirmdeleterequest')
def ConfirmDeleteRequest(id, type, title_year="", locked='unlocked'):
    oc = ObjectContainer(title2="Are you sure you would like to delete the request for " + title_year + "?")
    if Client.Platform == ClientPlatform.Android:  # If an android, add an empty first item because it gets truncated for some reason
        oc.add(DirectoryObject(key=None, title=""))
    oc.add(DirectoryObject(key=Callback(DeleteRequest, id=id, type=type, locked=locked), title="Yes", thumb=R('check.png')))
    oc.add(DirectoryObject(key=Callback(ViewRequest, id=id, type=type, locked=locked), title="No", thumb=R('x-mark.png')))
    return oc


@indirect
@route(PREFIX + '/deleterequest')
def DeleteRequest(id, type, locked='unlocked'):
    if id in Dict[type]:
        # oc = ObjectContainer(header=TITLE, message="Request was deleted!")
        message = "Request was deleted"
        del Dict[type][id]
        Dict.Save()
    else:
        # oc = ObjectContainer(header=TITLE, message="Request could not be deleted!")
        message = "Request could not be deleted"
    # oc.add(DirectoryObject(key=Callback(ViewRequests, locked=locked), title="Return to View Requests", thumb=R('return.png')))
    return ViewRequests(locked=locked, message=message)


@route(PREFIX + '/sendtocouchpotato')
def SendToCouchpotato(id, locked='unlocked'):
    if id not in Dict['movie']:
        return MessageContainer("Error", "The movie id was not found in the database")
    movie = Dict['movie'][id]
    if 'source' in movie and movie['source'] == 'tmdb':  # Check if id source is tmdb
        # we need to convert tmdb id to imdb
        json = JSON.ObjectFromURL(TMDB_API_URL + "movie/" + id + "?api_key=" + TMDB_API_KEY, headers={'Accept': 'application/json'})
        if 'imdb_id' in json and json['imdb_id']:
            imdb_id = json['imdb_id']
        else:
            imdb_id = ""
            oc = ObjectContainer(header=TITLE, message="Unable to get IMDB id for movie, add failed...")
            oc.add(DirectoryObject(key=Callback(ViewRequests, locked=locked), title="Return to View Requests"))
            return oc
    else:   #Assume we have an imdb_id by default
        imdb_id = id
    # we have an imdb id, add to couchpotato
    if not Prefs['couchpotato_url'].startswith("http"):
        couchpotato_url = "http://" + Prefs['couchpotato_url']
    else:
        couchpotato_url = Prefs['couchpotato_url']
    if not couchpotato_url.endswith("/"):
        couchpotato_url += "/"
    values = {'identifier': imdb_id}
    if Prefs['couchpotato_profile']:
        cat = JSON.ObjectFromURL(couchpotato_url + "api/" + Prefs['couchpotato_api'] + "/profile.list/")
        if cat['success']:
            for key in cat['list']:
                if key['label'] == Prefs['couchpotato_profile']:
                    values['profile_id'] = key['_id']
        else:
            Log.Debug("Unable to open up Couchpotato Profile List")
    if Prefs['couchpotato_category']:
        cat = JSON.ObjectFromURL(couchpotato_url + "api/" + Prefs['couchpotato_api'] + "/category.list/")
        if cat['success']:
            for key in cat['categories']:
                if key['label'] == Prefs['couchpotato_category']:
                    values['category_id'] = key['_id']
        else:
            Log.Debug("Unable to open up Couchpotato Category List")
    try:
        json = JSON.ObjectFromURL(couchpotato_url + "api/" + Prefs['couchpotato_api'] + "/movie.add/", values=values)
        if 'success' in json and json['success']:
            oc = ObjectContainer(header=TITLE, message="Movie Request Sent to CouchPotato!")
            Dict['movie'][id]['automated'] = True
        else:
            oc = ObjectContainer(header=TITLE, message="Movie Request failed!")
    except:
        oc = ObjectContainer(header=TITLE, message="Movie Request failed!")
    key = Dict['movie'][id]
    title_year = key['title'] + " (" + key['year'] + ")"
    if checkAdmin():
        oc.add(DirectoryObject(key=Callback(ConfirmDeleteRequest, id=id, type='movie', title_year=title_year, locked=locked), title="Delete Request"))
    oc.add(DirectoryObject(key=Callback(ViewRequests, locked=locked), title="Return to View Requests"))
    return oc


@route(PREFIX + '/sendtosonarr')
def SendToSonarr(id, locked='unlocked'):
    if not Prefs['sonarr_url'].startswith("http"):
        sonarr_url = "http://" + Prefs['sonarr_url']
    else:
        sonarr_url = Prefs['sonarr_url']
    if not sonarr_url.endswith("/"):
        sonarr_url = sonarr_url + "/"
    title = Dict['tv'][id]['title']
    api_header = {
        'X-Api-Key': Prefs['sonarr_api']
    }
    lookup_json = JSON.ObjectFromURL(sonarr_url + "api/Series/Lookup?term=tvdbid:" + id, headers=api_header)
    found_show = None
    for show in lookup_json:
        if show['tvdbId'] == id:
            found_show = show
    if not found_show:
        found_show = lookup_json[0]

    profile_json = JSON.ObjectFromURL(sonarr_url + "api/Profile", headers=api_header)
    profile_id = 1
    for profile in profile_json:
        if profile['name'] == Prefs['sonarr_profile']:
            profile_id = profile['id']
            break
    rootFolderPath = ""
    if Prefs['sonarr_path']:
        rootFolderPath = Prefs['sonarr_path']
    else:
        root = JSON.ObjectFromURL(sonarr_url + "api/Rootfolder", headers=api_header)
        if root:
            rootFolderPath = root[0]['path']

    Log.Debug("Profile id: " + str(profile_id))
    options = {'title': found_show['title'], 'tvdbId': found_show['tvdbId'], 'qualityProfileId': int(profile_id),
               'titleSlug': found_show['titleSlug'], 'rootFolderPath': rootFolderPath, 'seasons': found_show['seasons'], 'monitored': True}

    add_options = {'ignoreEpisodesWithFiles': False,
                   'ignoreEpisodesWithoutFiles': False,
                   'searchForMissingEpisodes': True
                   }

    if Prefs['sonarr_monitor'] == 'all':
        for season in options['seasons']:
            season['monitored'] = True
    elif Prefs['sonarr_monitor'] == 'future':
        add_options['ignoreEpisodesWithFiles'] = True
        add_options['ignoreEpisodesWithoutFiles'] = True
    elif Prefs['sonarr_monitor'] == 'latest':
        options['seasons'][len(options['seasons']) - 1]['monitored'] = True
    elif Prefs['sonarr_monitor'] == 'first':
        options['season'][1]['monitored'] = True
    elif Prefs['sonarr_monitor'] == 'missing':
        add_options['ignoreEpisodesWithFiles'] = True
    elif Prefs['sonarr_monitor'] == 'existing':
        add_options['ignoreEpisodesWithoutFiles'] = True
    elif Prefs['sonarr_monitor'] == 'none':
        options['monitored'] = False
    options['addOptions'] = add_options
    values = JSON.StringFromObject(options)
    try:
        HTTP.Request(sonarr_url + "api/Series", data=values, headers=api_header)
        oc = ObjectContainer(header=TITLE, message="Show has been sent to Sonarr.")
        Dict['tv'][id]['automated'] = True
    except:
        oc = ObjectContainer(header=TITLE, message="Could not send show to Sonarr!")
    if checkAdmin():
        oc.add(DirectoryObject(key=Callback(ConfirmDeleteRequest, id=id, type='tv', title_year=title, locked=locked), title="Delete Request"))
    oc.add(DirectoryObject(key=Callback(ViewRequests, locked=locked), title="Return to View Requests"))
    oc.add(DirectoryObject(key=Callback(MainMenu, locked=locked), title="Return to Main Menu"))
    return oc


@route(PREFIX + "/sendtosickrage")
def SendToSickrage(id, locked='unlocked'):
    if not Prefs['sickrage_url'].startswith("http"):
        sickrage_url = "http://" + Prefs['sickrage_url']
    else:
        sickrage_url = Prefs['sickrage_url']
    if not sickrage_url.endswith("/"):
        sickrage_url += "/"
    title = Dict['tv'][id]['title']
    data = {'tvdbid': id}
    if Prefs['sickrage_location']:
        data['location'] = Prefs['sickrage_location']
    if Prefs['sickrage_status']:
        data['status'] = Prefs['sickrage_status']
    if Prefs['sickrage_initial']:
        data['initial'] = Prefs['sickrage_initial']
    if Prefs['sickrage_archive']:
        data['archive'] = Prefs['sickrage_archive']

    try:
        resp = JSON.ObjectFromURL(sickrage_url + "api/" + Prefs['sickrage_api'] + "/", values=data)
        if 'success' in resp and resp['success']:
            oc = ObjectContainer(header=TITLE, message="Show added to SickRage")
            Dict['tv'][id]['automated'] = True
        else:
            oc = ObjectContainer(header=TITLE, message="Could not add show to SickRage!")
    except:
        oc = ObjectContainer(header=TITLE, message="Could not add show to SickRage!")
    if checkAdmin():
        oc.add(DirectoryObject(key=Callback(ConfirmDeleteRequest, id=id, type='tv', title_year=title, locked=locked), title="Delete Request"))
    oc.add(DirectoryObject(key=Callback(ViewRequests, locked=locked), title="Return to View Requests"))
    oc.add(DirectoryObject(key=Callback(MainMenu, locked=locked), title="Return to Main Menu"))
    return oc


@route(PREFIX + "/managechannel")
def ManageChannel(message=None, locked='locked'):
    if not checkAdmin():
        return MainMenu("Only an admin can manage the channel!")
    oc = ObjectContainer(header=TITLE, message=message)
    oc.add(DirectoryObject(key=Callback(ResetDict, locked=locked), title="Reset Dictionary Settings"))
    return oc


@route(PREFIX + "/resetdict")
def ResetDict(locked='locked', confirm='False'):
    if confirm == 'False':
        oc = ObjectContainer(header=TITLE,
                             message="Are you sure you would like to clear all saved info? This will clear all requests and user information.")
        oc.add(DirectoryObject(key=Callback(ResetDict, locked=locked, confirm='True'), title="Yes"))
        oc.add(DirectoryObject(key=Callback(ManageChannel, locked=locked), title="No"))
        return oc
    Dict.Reset()
    Dict['tv'] = {}
    Dict['movie'] = {}
    Dict['register'] = {}
    Dict['register_reset'] = Datetime.TimestampFromDatetime(Datetime.Now())
    if 'tv' not in Dict:
        Dict['tv'] = {}
    if 'movie' not in Dict:
        Dict['movie'] = {}
    if 'register' not in Dict:
        Dict['register'] = {}
        Dict['register_reset'] = Datetime.TimestampFromDatetime(Datetime.Now())

    return ManageChannel(message="Dictionary has been reset!", locked=locked)


# Notify user of requests
def notifyRequest(id, type, title="", message=""):
    if Prefs['pushbullet_api']:
        try:
            user = "A user"
            token = Request.Headers['X-Plex-Token']
            if token in Dict['register'] and Dict['register'][token]['nickname']:
                user = Dict['register'][token]['nickname']
            if type == 'movie':
                movie = Dict['movie'][id]
                title_year = movie['title'] + " (" + movie['year'] + ")"
                title = "Plex Request Channel - New Movie Request"
                message = user + " has requested a new movie.\n" + title_year + "\nIMDB id: " + id + "\nPoster: " + movie['poster']
            elif type == 'tv':
                tv = Dict['tv'][id]
                title = "Plex Request Channel - New TV Show Request"
                message = user + " has requested a new tv show.\n" + tv['title'] + "\nTVDB id: " + id + "\nPoster: " + tv['poster']
            else:
                return
            response = sendPushBullet(title, message)
            if response:
                Log.Debug("Pushbullet notification sent for :" + id)
        except Exception as e:
            Log.Debug("Pushbullet failed: " + e.message)
    if Prefs['pushover_user']:
        try:
            user = "A user"
            token = Request.Headers['X-Plex-Token']
            if token in Dict['register'] and Dict['register'][token]['nickname']:
                user = Dict['register'][token]['nickname']
            if type == 'movie':
                movie = Dict['movie'][id]
                title_year = movie['title'] + " (" + movie['year'] + ")"
                title = "Plex Request Channel - New Movie Request"
                message = user + " has requested a new movie.\n" + title_year + "\nIMDB id: " + id + "\nPoster: " + movie['poster']
            elif type == 'tv':
                tv = Dict['tv'][id]
                title = "Plex Request Channel - New TV Show Request"
                message = user + " has requested a new tv show.\n" + tv['title'] + "\nTVDB id: " + id + "\nPoster: " + tv['poster']
            else:
                return
            response = sendPushover(title, message)
            if response:
                Log.Debug("Pushover notification sent for :" + id)
        except Exception as e:
            Log.Debug("Pushover failed: " + e.message)
    if Prefs['email_to']:
        try:
            user = "A user"
            token = Request.Headers['X-Plex-Token']
            if token in Dict['register'] and Dict['register'][token]['nickname']:
                user = Dict['register'][token]['nickname']
            if type == 'movie':
                movie = Dict['movie'][id]
                title = movie['title'] + " (" + movie['year'] + ")"
                poster = movie['poster']
                id_type = "IMDB"
                subject = "Plex Request Channel - New Movie Request"
                summary = ""
                if movie['summary']:
                    summary = movie['summary'] + "<br>\n"
            elif type == 'tv':
                tv = Dict['tv'][id]
                title = tv['title']
                id_type = "TVDB"
                poster = tv['poster']
                subject = "Plex Request Channel - New TV Show Request"
                summary = ""
                if tv['summary']:
                    summary = tv['summary'] + "<br>\n"
            else:
                return
            message = user + " has made a new request! <br><br>\n" + \
                      "<font style='font-size:20px; font-weight:bold'> " + title + " </font><br>\n" + \
                      "(" + id_type + " id: " + id + ") <br>\n" + \
                      summary + \
                      "<Poster:><img src= '" + poster + "' width='300'>"
            sendEmail(subject, message, 'html')
            Log.Debug("Email notification sent for: " + id)
        except Exception as e:
            Log.Debug("Email failed: " + e.message)


def Notify(title, body):
    if Prefs['email_to']:
        try:
            if not sendEmail(title, body, 'html'):
                Log.Debug("Email notification sent")
        except Exception as e:
            Log.Debug("Email failed: " + e.message)
    if Prefs['pushbullet_api']:
        try:
            if sendPushBullet(title, body):
                Log.Debug("Pushbullet notification sent")
        except Exception as e:
            Log.Debug("PushBullet failed: " + e.message)
    if Prefs['pushover_user']:
        try:
            if sendPushover(title, body):
                Log.Debug("Pushover notification sent")
        except Exception as e:
            Log.Debug("Pushover failed: " + e.message)


def sendPushBullet(title, body):
    api_header = {'Authorization': 'Bearer ' + Prefs['pushbullet_api'],
                  'Content-Type': 'application/json'
                  }
    data = {'type': 'note', 'title': title, 'body': body}
    values = JSON.StringFromObject(data)
    return HTTP.Request(PUSHBULLET_API_URL + "pushes", data=values, headers=api_header)


def sendPushover(title, message):
    data = {'token': Prefs['pushover_api'], 'user': Prefs['pushover_user'], 'title': title, 'message': message}
    return HTTP.Request(PUSHOVER_API_URL, values=data)


# noinspection PyUnresolvedReferences
def sendEmail(subject, body, type='html'):
    from email.MIMEText import MIMEText
    from email.MIMEMultipart import MIMEMultipart
    import smtplib

    msg = MIMEMultipart()
    msg['From'] = Prefs['email_from']
    msg['To'] = Prefs['email_to']
    msg['Subject'] = subject
    msg.attach(MIMEText(body, type))
    server = smtplib.SMTP(Prefs['email_server'], int(Prefs['email_port']))
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(Prefs['email_username'], Prefs['email_password'])
    text = msg.as_string()
    senders = server.sendmail(Prefs['email_from'], Prefs['email_to'], text)
    server.quit()
    return senders


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
