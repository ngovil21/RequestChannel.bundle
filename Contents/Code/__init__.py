from Keyboard import Keyboard, DUMB_KEYBOARD_CLIENTS, NO_MESSAGE_CONTAINER_CLIENTS

import re


TITLE = 'Plex Request Channel'
PREFIX = '/video/plexrequestchannel'

ART = 'art-default.jpg'
ICON = 'plexrequestchannel.png'

VERSION = "0.6.3"
CHANGELOG_URL = "https://raw.githubusercontent.com/ngovil21/PlexRequestChannel.bundle/master/CHANGELOG"

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
########################################################

### Notification Constants #############################
PUSHBULLET_API_URL = "https://api.pushbullet.com/v2/"
PUSHOVER_API_URL = "https://api.pushover.net/1/messages.json"
PUSHOVER_API_KEY = "ajMtuYCg8KmRQCNZK2ggqaqiBw2UHi"
########################################################

TV_SHOW_OBJECT_FIX_CLIENTS = ["Android", "Samsung"]


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

    if 'tv' not in Dict:
        Dict['tv'] = {}
    if 'movie' not in Dict:
        Dict['movie'] = {}
    if 'register' not in Dict:
        Dict['register'] = {}
        Dict['register_reset'] = Datetime.TimestampFromDatetime(Datetime.Now())
    if 'blocked' not in Dict:
        Dict['blocked'] = []
    if 'sonarr_users' not in Dict:
        Dict['sonarr_users'] = []
    Dict.Save()


def ValidatePrefs():
    return


###################################################################################################
# This tells Plex how to list you in the available channels and what type of channels this is
@handler(PREFIX, TITLE, art=ART, thumb=ICON)
@route(PREFIX + '/mainmenu')
def MainMenu(locked='locked', message=None, title1=TITLE, title2="Main Menu"):
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
            key=Callback(Keyboard, callback=SearchMovie, parent=MainMenu, locked=locked, title="Search for Movie",
                         message="Enter the name of the movie"),
            title="Request a Movie"))
        oc.add(DirectoryObject(
            key=Callback(Keyboard, callback=SearchTV, parent=MainMenu, locked=locked, title="Search for TV Show",
                         message="Enter the name of the TV Show"),
            title="Request a TV Show"))
    elif Client.Product == "Plex Web":  # Plex Web does not create a popup input directory object, so use an intermediate menu
        oc.add(DirectoryObject(key=Callback(AddNewMovie, title="Request a Movie", locked=locked), title="Request a Movie"))
        oc.add(DirectoryObject(key=Callback(AddNewTVShow, locked=locked), title="Request a TV Show"))
    else:  # All other clients
        oc.add(
            InputDirectoryObject(key=Callback(SearchMovie, locked=locked), title="Search for Movie", prompt="Enter the name of the movie:"))
        oc.add(
            InputDirectoryObject(key=Callback(SearchTV, locked=locked), title="Search for TV Show", prompt="Enter the name of the TV Show:"))
    if Prefs['usersviewrequests'] or is_admin:
        if locked == 'unlocked' or Prefs['password'] is None or Prefs['password'] == "":
            oc.add(DirectoryObject(key=Callback(ViewRequests, locked='unlocked'), title="View Requests"))  # No password needed this session
        else:
            oc.add(DirectoryObject(key=Callback(ViewRequestsPassword, locked='locked'),
                                   title="View Requests"))  # Set View Requests to locked and ask for password
    if Prefs['sonarr_api'] and (is_admin or token in Dict['sonarr_users']):
        oc.add(DirectoryObject(key=Callback(ManageSonarr, locked=locked), title="Manage Sonarr"))
    oc.add(DirectoryObject(key=Callback(ReportProblem, locked=locked), title="Report a Problem"))
    if is_admin:
        oc.add(DirectoryObject(key=Callback(ManageChannel, locked=locked), title="Manage Channel"))
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
        oc.add(DirectoryObject(key=Callback(Keyboard, callback=RegisterName, parent=MainMenu, locked=locked), title="Enter your name or nickname"))
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
    return MainMenu(message="Your device has been registered. Thank you.", locked=locked, title1="Main Menu", title2="Registered")


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


@route(PREFIX + '/addnewmovie')
def AddNewMovie(title="Request a Movie", locked='unlocked'):
    oc = ObjectContainer(header=TITLE, message="Please enter the movie name in the searchbox and press enter.")
    if Client.Platform in NO_MESSAGE_CONTAINER_CLIENTS or Client.Product in NO_MESSAGE_CONTAINER_CLIENTS:
        oc.message = None
    if Client.Product in DUMB_KEYBOARD_CLIENTS or Client.Platform in DUMB_KEYBOARD_CLIENTS:
        Log.Debug("Client does not support Input. Using DumbKeyboard")
        # oc.add(DirectoryObject(key="", title=""))
        # DumbKeyboard(prefix=PREFIX, oc=oc, callback=SearchMovie, dktitle=title, dkthumb=R('search.png'), locked=locked)
        oc.add(DirectoryObject(key=Callback(Keyboard, callback=SearchMovie, parent=MainMenu, locked=locked), title=title, thumb=R('search.png')))
    else:
        oc.add(
            InputDirectoryObject(key=Callback(SearchMovie, locked=locked), title=title, prompt="Enter the name of the movie:", thumb=R('search.png')))
    return oc


@route(PREFIX + '/searchmovie')
def SearchMovie(title="Search Results", query="", locked='unlocked'):
    oc = ObjectContainer(title1=title, title2=query, content=ContainerContent.Shows, view_group="Details")
    query = String.Quote(query, usePlus=True)
    token = Request.Headers['X-Plex-Token']
    if Prefs['weekly_limit'] and int(Prefs['weekly_limit']) > 0 and not checkAdmin():

        if Dict['register'].get(token, None) and Dict['register'][token]['requests'] >= int(Prefs['weekly_limit']):
            return MainMenu(message="Sorry you have reached your weekly request limit of " + Prefs['weekly_limit'] + ".", locked=locked,
                            title1="Main Menu", title2="Weekly Limit")
    if token in Dict['blocked']:
        return MainMenu(message="Sorry you have been blocked.", locked=locked,
                        title1="Main Menu", title2="User Blocked")
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
                oc.add(TVShowObject(
                    key=Callback(ConfirmMovieRequest, movie_id=key['id'], source='tmdb', title=key['title'], year=year, poster=thumb, backdrop=art,
                                 summary=key['overview'], locked=locked), rating_key=key['id'], title=title_year, thumb=thumb,
                    summary=key['overview'], art=art))
        else:
            if Client.Platform in NO_MESSAGE_CONTAINER_CLIENTS or Client.Product in NO_MESSAGE_CONTAINER_CLIENTS:
                oc = ObjectContainer(title2="No results")
            else:
                oc = ObjectContainer(header=TITLE, message="Sorry there were no results found for your search.")
            Log.Debug("No Results Found")
            if Client.Product in DUMB_KEYBOARD_CLIENTS or Client.Platform in DUMB_KEYBOARD_CLIENTS:
                Log.Debug("Client does not support Input. Using DumbKeyboard")
                # oc.add(DirectoryObject(key="", title=""))
                # DumbKeyboard(prefix=PREFIX, oc=oc, callback=SearchMovie, dktitle="Search Again", dkthumb=R('search.png'), locked=locked)
                oc.add(DirectoryObject(key=Callback(Keyboard, callback=SearchMovie, parent=MainMenu, locked=locked), title="Search Again",
                                       thumb=R('search.png')))
            else:
                oc.add(InputDirectoryObject(key=Callback(SearchMovie, locked=locked), title="Search Again",
                                            prompt="Enter the name of the movie:"))
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
                    key=Callback(ConfirmMovieRequest, movie_id=key['imdbID'], source='imdb', title=key['Title'], year=key['Year'],
                                 poster=key['Poster'],
                                 locked=locked), rating_key=key['imdbID'], title=title_year, thumb=thumb))
        else:
            Log.Debug("No Results Found")
            if Client.Platform in NO_MESSAGE_CONTAINER_CLIENTS or Client.Product in NO_MESSAGE_CONTAINER_CLIENTS:
                oc = ObjectContainer(title2="No results")
            else:
                oc = ObjectContainer(header=TITLE, message="Sorry there were no results found for your search.")
            if Client.Product in DUMB_KEYBOARD_CLIENTS or Client.Platform in DUMB_KEYBOARD_CLIENTS:
                Log.Debug("Client does not support Input. Using DumbKeyboard")
                # DumbKeyboard(prefix=PREFIX, oc=oc, callback=SearchMovie, dktitle="Search Again", dkthumb=R('search.png'), locked=locked)
                oc.add(DirectoryObject(key=Callback(Keyboard, callback=SearchMovie, parent=MainMenu, locked=locked), title="Search Again",
                                       thumb=R('search.png')))
            else:
                oc.add(InputDirectoryObject(key=Callback(SearchMovie, locked=locked), title="Search Again",
                                            prompt="Enter the name of the movie:"))
            oc.add(DirectoryObject(key=Callback(MainMenu, locked=locked), title="Back to Main Menu", thumb=R('return.png')))
            return oc
    if Client.Product in DUMB_KEYBOARD_CLIENTS or Client.Platform in DUMB_KEYBOARD_CLIENTS:
        Log.Debug("Client does not support Input. Using DumbKeyboard")
        # DumbKeyboard(prefix=PREFIX, oc=oc, callback=SearchMovie, dktitle="Search Again", dkthumb=R('search.png'), locked=locked)
        oc.add(DirectoryObject(key=Callback(Keyboard, callback=SearchMovie, parent=MainMenu, locked=locked), title="Search Again",
                               thumb=R('search.png')))
    else:
        oc.add(InputDirectoryObject(key=Callback(SearchMovie, locked=locked), title="Search Again",
                                    prompt="Enter the name of the movie:", thumb=R('search.png')))
    oc.add(DirectoryObject(key=Callback(MainMenu, locked=locked), title="Return to Main Menu", thumb=R('return.png')))
    return oc


@route(PREFIX + '/confirmmovierequest')
def ConfirmMovieRequest(movie_id, title, source='', year="", poster="", backdrop="", summary="", locked='unlocked'):
    title_year = title + " " + "(" + year + ")"
    if Client.Platform in NO_MESSAGE_CONTAINER_CLIENTS or Client.Product in NO_MESSAGE_CONTAINER_CLIENTS:
        oc = ObjectContainer(title1="Confirm Movie Request", title2=title_year + "?")
    else:
        oc = ObjectContainer(title1="Confirm Movie Request", title2=title_year + "?",
                             header=TITLE, message="Request movie " + title_year + "?")
    found_match = False
    try:
        local_search = XML.ElementFromURL(url="http://127.0.0.1:32400/search?local=1&query=" + String.Quote(title), headers=Request.Headers)
        if local_search:
            # Log.Debug(XML.StringFromElement(local_search))
            videos = local_search.xpath("//Video")
            for video in videos:
                if video.attrib['title'] == title and video.attrib['year'] == year and video.attrib['type'] == 'movie':
                    Log.Debug("Possible match found: " + str(video.attrib['ratingKey']))
                    summary = "(In Library: " + video.attrib['librarySectionTitle'] + ") " + (
                        video.attrib['summary'] if video.attrib['summary'] else "")
                    oc.add(TVShowObject(key=Callback(MainMenu, locked=locked, message="Movie already in library.", title1="In Library", title2=title),
                                        rating_key=video.attrib['ratingKey'], title="+ " + title, summary=summary, thumb=video.attrib['thumb']))
                    found_match = True
                    break
    except:
        pass
    if found_match:
        if Client.Platform in NO_MESSAGE_CONTAINER_CLIENTS or Client.Product in NO_MESSAGE_CONTAINER_CLIENTS:
            oc.title1 = "Movie Already Exists"
        else:
            oc.message = "Movie appears to already exist in the library. Are you sure you would still like to request it?"
    if not found_match and Client.Platform in TV_SHOW_OBJECT_FIX_CLIENTS:  # If an android, add an empty first item because it gets truncated for some reason
        oc.add(DirectoryObject(key=None, title=""))
    oc.add(DirectoryObject(
        key=Callback(AddMovieRequest, movie_id=movie_id, source=source, title=title, year=year, poster=poster, backdrop=backdrop, summary=summary,
                     locked=locked), title="Add Anyways" if found_match else "Yes", thumb=R('check.png')))
    oc.add(DirectoryObject(key=Callback(MainMenu, locked=locked), title="No", thumb=R('x-mark.png')))

    return oc


@route(PREFIX + '/addmovierequest')
def AddMovieRequest(movie_id, title, source='', year="", poster="", backdrop="", summary="", locked='unlocked'):
    if movie_id in Dict['movie']:
        Log.Debug("Movie is already requested")
        return MainMenu(locked=locked, message="Movie has already been requested", title1=title, title2="Already Requested")
    else:
        user = ""
        token = Request.Headers['X-Plex-Token']
        if token in Dict['register'] and Dict['register'][token]['nickname']:
            user = Dict['register'][token]['nickname']
            Dict['register'][token]['requests'] = Dict['register'][token]['requests'] + 1
        title_year = title + " (" + year + ")"
        Dict['movie'][movie_id] = {'type': 'movie', 'id': movie_id, 'source': source, 'title': title, 'year': year, 'title_year': title_year,
                                   'poster': poster,
                                   'backdrop': backdrop, 'summary': summary, 'user': user, 'automated': False}
        Dict.Save()
        if Prefs['couchpotato_autorequest']:
            SendToCouchpotato(movie_id)
        notifyRequest(req_id=movie_id, req_type='movie')
        return MainMenu(locked=locked, message="Movie has been requested", title1="Main Menu", title2="Movie Requested")


# TVShow Functions


@route(PREFIX + '/addtvshow')
def AddNewTVShow(title="Request a TV Show", locked='unlocked'):
    token = Request.Headers['X-Plex-Token']
    if Prefs['weekly_limit'] and int(Prefs['weekly_limit'] > 0) and not checkAdmin():
        if token in Dict['register'] and Dict['register'][token]['requests'] >= int(Prefs['weekly_limit']):
            return MainMenu(message="Sorry you have reached your weekly request limit of " + Prefs['weekly_limit'] + ".", locked=locked,
                            title1="Main Menu", title2="Weekly Limit")
    if token in Dict['blocked']:
        return MainMenu(message="Sorry you have been blocked.", locked=locked,
                        title1="Main Menu", title2="User Blocked")
    if Client.Platform == "iOS" or Client.Product == "Plex for iOS":
        oc = ObjectContainer(title2=title)
    else:
        oc = ObjectContainer(header=TITLE, message="Please enter the name of the TV Show in the search box and press enter.")
    if Client.Product in DUMB_KEYBOARD_CLIENTS or Client.Platform in DUMB_KEYBOARD_CLIENTS:
        Log.Debug("Client does not support Input. Using DumbKeyboard")
        # DumbKeyboard(prefix=PREFIX, oc=oc, callback=SearchTV, dktitle="Request a TV Show", dkthumb=R('search.png'), locked=locked)
        oc.add(DirectoryObject(key=Callback(Keyboard, callback=SearchTV, parent=MainMenu, locked=locked), title="Request a TV Show",
                               thumb=R('search.png')))
    else:
        oc.add(InputDirectoryObject(key=Callback(SearchTV, locked=locked), title="Request a TV Show", prompt="Enter the name of the TV Show:",
                                    thumb=R('search.png')))
    return oc


@route(PREFIX + '/searchtv')
def SearchTV(query, locked='unlocked'):
    oc = ObjectContainer(title1="Search Results", title2=query, content=ContainerContent.Shows, view_group="Details")
    query = String.Quote(query, usePlus=True)
    xml = XML.ElementFromURL(TVDB_API_URL + "GetSeries.php?seriesname=" + query)
    series = xml.xpath("//Series")
    if len(series) == 0:
        if Client.Platform in NO_MESSAGE_CONTAINER_CLIENTS or Client.Product in NO_MESSAGE_CONTAINER_CLIENTS:
            oc = ObjectContainer(title2="No Results")
        else:
            oc = ObjectContainer(header=TITLE, message="Sorry there were no results found.")
        if Client.Product in DUMB_KEYBOARD_CLIENTS or Client.Platform in DUMB_KEYBOARD_CLIENTS:
            Log.Debug("Client does not support Input. Using DumbKeyboard")
            # DumbKeyboard(prefix=PREFIX, oc=oc, callback=SearchTV, dktitle="Search Again", dkthumb=R('search.png'), locked=locked)
            oc.add(DirectoryObject(key=Callback(Keyboard, callback=SearchTV, parent=MainMenu, locked=locked), title="Search Again",
                                   thumb=R('search.png')))
        else:
            oc.add(InputDirectoryObject(key=Callback(SearchTV, locked=locked), title="Search Again", prompt="Enter the name of the TV Show:",
                                        thumb=R('search.png')))
        oc.add(DirectoryObject(key=Callback(MainMenu, locked=locked), title="Return to Main Menu", thumb=R('return.png')))
        return oc
    count = 0
    for serie in series:
        series_id = ""
        title = ""
        year = ""
        poster = ""
        summary = ""
        for child in serie.getchildren():
            if child.tag.lower() == "seriesid" and child.text:
                series_id = child.text
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
                serie_page = XML.ElementFromURL(TVDB_API_URL + TVDB_API_KEY + "/series/" + series_id)
                poster_text = serie_page.xpath("//Series/poster/text()")
                if poster_text:
                    poster = TVDB_BANNER_URL + poster_text[0]
            except Exception as e:
                Log.Debug(e)
            count += 1
        if series_id == "":
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
            TVShowObject(
                key=Callback(ConfirmTVRequest, series_id=series_id, source='tvdb', title=title, year=year, poster=poster, summary=summary,
                             locked=locked),
                rating_key=series_id, title=title_year, summary=summary, thumb=thumb))
    if Client.Product in DUMB_KEYBOARD_CLIENTS or Client.Platform in DUMB_KEYBOARD_CLIENTS:
        Log.Debug("Client does not support Input. Using DumbKeyboard")
        # DumbKeyboard(prefix=PREFIX, oc=oc, callback=SearchTV, dktitle="Search Again", dkthumb=R('search.png'), locked=locked)
        oc.add(
            DirectoryObject(key=Callback(Keyboard, callback=SearchTV, parent=MainMenu, locked=locked), title="Search Again", thumb=R('search.png')))
    else:
        oc.add(InputDirectoryObject(key=Callback(SearchTV, locked=locked), title="Search Again", prompt="Enter the name of the TV Show:",
                                    thumb=R('search.png')))
    oc.add(DirectoryObject(key=Callback(MainMenu, locked=locked), title="Return to Main Menu", thumb=R('return.png')))
    return oc


@route(PREFIX + '/confirmtvrequest')
def ConfirmTVRequest(series_id, title, source="", year="", poster="", backdrop="", summary="", locked='unlocked'):
    if year:
        title_year = title + " " + "(" + year + ")"
    else:
        title_year = title

    if Client.Platform == "iOS" or Client.Product == "Plex for iOS":
        oc = ObjectContainer(title1="Confirm TV Request", title2=title_year + "?")
    else:
        oc = ObjectContainer(title1="Confirm TV Request", title2="Are you sure you would like to request the TV Show " + title_year + "?",
                             header=TITLE, message="Request tv show " + title_year + "?")

    found_match = False
    try:
        local_search = XML.ElementFromURL(url="http://127.0.0.1:32400/search?local=1&query=" + String.Quote(title), headers=Request.Headers)
        if local_search:
            # Log.Debug(XML.StringFromElement(local_search))
            videos = local_search.xpath("//Directory")
            for video in videos:
                video_attr = video.attrib
                if video_attr['title'] == title and video_attr['year'] == year and video_attr['type'] == 'show':
                    Log.Debug("Possible match found: " + str(video_attr['ratingKey']))
                    summary = "(In Library: " + video_attr['librarySectionTitle'] + ") " + (video_attr['summary'] if video_attr['summary'] else "")
                    oc.add(
                        TVShowObject(key=Callback(MainMenu, locked=locked, message="TV Show already in library.", title1="In Library", title2=title),
                                     rating_key=video_attr['ratingKey'], title="+ " + title, summary=summary, thumb=video_attr['thumb']))
                    found_match = True
                    break
    except:
        pass

    if found_match:
        if Client.Platform in NO_MESSAGE_CONTAINER_CLIENTS or Client.Product in NO_MESSAGE_CONTAINER_CLIENTS:
            oc.title1 = "Show Already Exists"
        else:
            oc.message = "TV Show appears to already exist in the library. Are you sure you would still like to request it?"
    if not found_match and Client.Platform in TV_SHOW_OBJECT_FIX_CLIENTS:  # If an android, add an empty first item because it gets truncated for some reason
        oc.add(DirectoryObject(key=None, title=""))
    oc.add(DirectoryObject(
        key=Callback(AddTVRequest, series_id=series_id, source=source, title=title, year=year, poster=poster, backdrop=backdrop, summary=summary,
                     locked=locked), title="Add Anyways" if found_match else "Yes", thumb=R('check.png')))
    oc.add(DirectoryObject(key=Callback(MainMenu, locked=locked), title="No", thumb=R('x-mark.png')))

    return oc


@indirect
@route(PREFIX + '/addtvrequest')
def AddTVRequest(series_id, title, source='', year="", poster="", backdrop="", summary="", locked='unlocked'):
    if series_id in Dict['tv']:
        Log.Debug("TV Show is already requested")
        return MainMenu(locked=locked, message="TV Show has already been requested", title1=title, title2="Already Requested")
    else:
        token = Request.Headers['X-Plex-Token']
        user = ""
        if token in Dict['register'] and Dict['register'][token]['nickname']:
            user = Dict['register'][token]['nickname']
            Dict['register'][token]['requests'] = Dict['register'][token]['requests'] + 1
        Dict['tv'][series_id] = {'type': 'tv', 'id': series_id, 'source': source, 'title': title, 'year': year, 'poster': poster,
                                 'backdrop': backdrop, 'summary': summary, 'user': user, 'automated': False}
        Dict.Save()
        if Prefs['sonarr_autorequest'] and Prefs['sonarr_url'] and Prefs['sonarr_api']:
            SendToSonarr(tvdbid=series_id)
        if Prefs['sickbeard_autorequest'] and Prefs['sickbeard_url'] and Prefs['sickbeard_api']:
            SendToSickbeard(series_id)
        notifyRequest(req_id=series_id, req_type='tv')
        return MainMenu(locked=locked, message="TV Show has been requested", title1=title, title2="Requested")


# Request Functions

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
    if Client.Platform in TV_SHOW_OBJECT_FIX_CLIENTS:  # If an android, add an empty first item because it gets truncated for some reason
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
    title_year = key['title'] + " (" + key['year'] + ")" if not re.search(" \(/d/d/d/d\)") else key['title']           #If there is already a year in the title, just use title
    oc = ObjectContainer(title2=title_year)
    if Client.Platform in TV_SHOW_OBJECT_FIX_CLIENTS:  # If an android, add an empty first item because it gets truncated for some reason
        oc.add(DirectoryObject(key=None, title=""))
    if Client.Product == "Plex Web":                    #If Plex Web then add an item with the poster
        oc.add(TVShowObject(key=Callback(ViewRequest, req_id=req_id, req_type=req_type, locked=locked), rating_key=req_id, thumb=key['poster'], summary=key['summary'], title=title_year))
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
            oc.add(DirectoryObject(
                key=Callback(SendToSonarr, tvdbid=req_id, locked=locked, callback=Callback(ViewRequest, req_id=req_id, req_type='tv', locked=locked)),
                title="Send to Sonarr", thumb=R('sonarr.png')))
        if Prefs['sickbeard_url'] and Prefs['sickbeard_api']:
            oc.add(DirectoryObject(key=Callback(SendToSickbeard, series_id=req_id, locked=locked), title="Send to " + Prefs['sickbeard_fork'],
                                   thumb=R(Prefs['sickbeard_fork'].lower() + '.png')))
    oc.add(DirectoryObject(key=Callback(ViewRequests, locked=locked), title="Return to View Requests", thumb=R('return.png')))
    return oc


@route(PREFIX + '/confirmdeleterequest')
def ConfirmDeleteRequest(req_id, req_type, title_year="", locked='unlocked'):
    oc = ObjectContainer(title2="Are you sure you would like to delete the request for " + title_year + "?")
    if Client.Platform in TV_SHOW_OBJECT_FIX_CLIENTS:  # If an android, add an empty first item because it gets truncated for some reason
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


# CouchPotato Functions


@route(PREFIX + '/sendtocouchpotato')
def SendToCouchpotato(movie_id, locked='unlocked'):
    if movie_id not in Dict['movie']:
        return MessageContainer("Error", "The movie id was not found in the database")
    movie = Dict['movie'][movie_id]
    if 'source' in movie and movie['source'] == 'tmdb':  # Check if id source is tmdb
        # we need to convert tmdb id to imdb
        json = JSON.ObjectFromURL(TMDB_API_URL + "movie/" + movie_id + "?api_key=" + TMDB_API_KEY, headers={'Accept': 'application/json'})
        if 'imdb_id' in json and json['imdb_id']:
            imdb_id = json['imdb_id']
        else:
            imdb_id = ""
            if Client.Platform in NO_MESSAGE_CONTAINER_CLIENTS or Client.Product in NO_MESSAGE_CONTAINER_CLIENTS:
                oc = ObjectContainer(title1="CouchPotato", title2="Send Failed")
            else:
                oc = ObjectContainer(header=TITLE, message="Unable to get IMDB id for movie, add failed...")
            oc.add(DirectoryObject(key=Callback(ViewRequests, locked=locked), title="Return to View Requests"))
            return oc
    else:  # Assume we have an imdb_id by default
        imdb_id = movie_id
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
            if Client.Platform in NO_MESSAGE_CONTAINER_CLIENTS or Client.Product in NO_MESSAGE_CONTAINER_CLIENTS:
                oc = ObjectContainer(title1="Couchpotato", title2="Success")
            else:
                oc = ObjectContainer(header=TITLE, message="Movie Request Sent to CouchPotato!")
            Dict['movie'][movie_id]['automated'] = True
        else:
            if Client.Platform in NO_MESSAGE_CONTAINER_CLIENTS or Client.Product in NO_MESSAGE_CONTAINER_CLIENTS:
                oc = ObjectContainer(title1="CouchPotato", title2="Send Failed")
            else:
                oc = ObjectContainer(header=TITLE, message="CouchPotato Send Failed!")
    except:
        if Client.Platform in NO_MESSAGE_CONTAINER_CLIENTS or Client.Product in NO_MESSAGE_CONTAINER_CLIENTS:
            oc = ObjectContainer(title1="CouchPotato", title2="Send Failed")
        else:
            oc = ObjectContainer(header=TITLE, message="CouchPotato Send Failed!")
    key = Dict['movie'][movie_id]
    title_year = key['title'] + " (" + key['year'] + ")"
    if checkAdmin():
        oc.add(DirectoryObject(key=Callback(ConfirmDeleteRequest, req_id=movie_id, req_type='movie', title_year=title_year, locked=locked),
                               title="Delete Request"))
    oc.add(DirectoryObject(key=Callback(ViewRequests, locked=locked), title="Return to View Requests"))
    return oc


# Sonarr Methods


@route(PREFIX + '/sendtosonarr')
def SendToSonarr(tvdbid, locked='unlocked', callback=None):
    if not Prefs['sonarr_url'].startswith("http"):
        sonarr_url = "http://" + Prefs['sonarr_url']
    else:
        sonarr_url = Prefs['sonarr_url']
    if not sonarr_url.endswith("/"):
        sonarr_url += "/"
    title = Dict['tv'][tvdbid]['title']
    api_header = {
        'X-Api-Key': Prefs['sonarr_api']
    }
    series_id = ShowExists(tvdbid)
    if series_id:
        Dict['tv'][tvdbid]['automated'] = True
        return ManageSonarrShow(series_id=series_id, locked=locked, callback=callback)
    lookup_json = JSON.ObjectFromURL(sonarr_url + "api/Series/Lookup?term=tvdbid:" + tvdbid, headers=api_header)
    found_show = None
    for show in lookup_json:
        if show['tvdbId'] == series_id:
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
        if Client.Platform in NO_MESSAGE_CONTAINER_CLIENTS or Client.Product in NO_MESSAGE_CONTAINER_CLIENTS:
            oc = ObjectContainer(title1="Sonarr", title2="Success")
        else:
            oc = ObjectContainer(header=TITLE, message="Show has been sent to ")
        Dict['tv'][series_id]['automated'] = True
    except:
        if Client.Platform in NO_MESSAGE_CONTAINER_CLIENTS or Client.Product in NO_MESSAGE_CONTAINER_CLIENTS:
            oc = ObjectContainer(title1="Sonarr", title2="Send Failed")
        else:
            oc = ObjectContainer(header=TITLE, message="Could not send show to Sonarr!")
    if checkAdmin():
        oc.add(DirectoryObject(key=Callback(ConfirmDeleteRequest, req_id=series_id, req_type='tv', title_year=title, locked=locked),
                               title="Delete Request"))
    oc.add(DirectoryObject(key=Callback(ViewRequests, locked=locked), title="Return to View Requests"))
    oc.add(DirectoryObject(key=Callback(MainMenu, locked=locked), title="Return to Main Menu"))
    return oc


@route(PREFIX + '/managesonarr')
def ManageSonarr(locked='unlocked'):
    oc = ObjectContainer(title1=TITLE, title2="Manage Sonarr")
    if not Prefs['sonarr_url'].startswith("http"):
        sonarr_url = "http://" + Prefs['sonarr_url']
    else:
        sonarr_url = Prefs['sonarr_url']
    if sonarr_url.endswith("/"):
        sonarr_url = sonarr_url[:-1]
    api_header = {
        'X-Api-Key': Prefs['sonarr_api']
    }
    try:
        shows = JSON.ObjectFromURL(sonarr_url + "/api/Series", headers=api_header)
    except Exception as e:
        Log.Debug(e.message)
        return MessageContainer(header=TITLE, message="Error retrieving Sonarr Shows")
    for show in shows:
        poster = None
        for image in show['images']:
            if image['coverType'] == 'poster':
                poster = sonarr_url + image['url'][image['url'].find('/MediaCover/'):]
        oc.add(TVShowObject(key=Callback(ManageSonarrShow, series_id=show['id'], title=show['title'], locked=locked), rating_key=show['tvdbId'],
                            title=show['title'], thumb=poster, summary=show['overview']))
    oc.objects.sort(key=lambda obj: obj.title.lower())
    oc.add(DirectoryObject(key=Callback(MainMenu, locked=locked), title="Return to Main Menu"))
    return oc


@route(PREFIX + '/managesonarrshow')
def ManageSonarrShow(series_id, title="", locked='unlocked', callback=None, message=None):
    if not Prefs['sonarr_url'].startswith("http"):
        sonarr_url = "http://" + Prefs['sonarr_url']
    else:
        sonarr_url = Prefs['sonarr_url']
    if sonarr_url.endswith("/"):
        sonarr_url = sonarr_url[:-1]
    api_header = {
        'X-Api-Key': Prefs['sonarr_api']
    }
    try:
        show = JSON.ObjectFromURL(sonarr_url + "/api/Series/" + str(series_id), headers=api_header)
    except Exception as e:
        Log.Debug(e.message)
        return MessageContainer(header=TITLE, message="Error retrieving Sonarr Show: " + title)
    if Client.Platform in NO_MESSAGE_CONTAINER_CLIENTS or Client.Product in NO_MESSAGE_CONTAINER_CLIENTS:
        oc = ObjectContainer(title1="Manage Sonarr Show", title2=show['title'])
    else:
        oc = ObjectContainer(title1="Manage Sonarr Show", title2=show['title'], header=TITLE if message else None, message=message)
    if callback:
        oc.add(DirectoryObject(key=callback, title="Go Back", thumb=None))
    else:
        oc.add(DirectoryObject(key=Callback(ManageSonarr, locked=locked), title="Return to Shows"))
    oc.add(DirectoryObject(key=Callback(SonarrMonitorShow, series_id=series_id, seasons='all', locked=locked, callback=callback),
                           title="Monitor All Seasons", thumb=None))
    # Log.Debug(show['seasons'])
    for season in show['seasons']:
        season_number = int(season['seasonNumber'])
        mark = "* " if season['monitored'] else ""
        oc.add(DirectoryObject(key=Callback(ManageSonarrSeason, series_id=series_id, season=season_number, locked=locked, callback=callback),
                               title=mark + ("Season " + str(season_number) if season_number > 0 else "Specials"), summary=show['overview'],
                               thumb=None))
    return oc


@route(PREFIX + '/managesonarrseason')
def ManageSonarrSeason(series_id, season, locked='unlocked', message=None, callback=None):
    if not Prefs['sonarr_url'].startswith("http"):
        sonarr_url = "http://" + Prefs['sonarr_url']
    else:
        sonarr_url = Prefs['sonarr_url']
    if sonarr_url.endswith("/"):
        sonarr_url = sonarr_url[:-1]
    api_header = {
        'X-Api-Key': Prefs['sonarr_api']
    }
    if Client.Platform in NO_MESSAGE_CONTAINER_CLIENTS or Client.Product in NO_MESSAGE_CONTAINER_CLIENTS:
        oc = ObjectContainer(title1="Manage Season", title2="Season " + str(season))
    else:
        oc = ObjectContainer(title1="Manage Season", title2="Season " + str(season), header=TITLE if message else None, message=message)
    if callback:
        oc.add(DirectoryObject(key=callback, title="Go Back"))
    oc.add(DirectoryObject(key=Callback(ManageSonarrShow, series_id=series_id, locked=locked, callback=callback), title="Return to Seasons"))
    oc.add(DirectoryObject(key=Callback(SonarrMonitorShow, series_id=series_id, seasons=str(season), locked=locked, callback=callback),
                           title="Get All Episodes", thumb=None))
    # data = JSON.StringFromObject({'seriesId': series_id})
    episodes = JSON.ObjectFromURL(sonarr_url + "/api/Episode/?seriesId=" + str(series_id), headers=api_header)
    # Log.Debug(JSON.StringFromObject(episodes))
    for episode in episodes:
        if not episode['seasonNumber'] == int(season):
            continue
        marked = "* " if episode['monitored'] else ""
        oc.add(
            DirectoryObject(key=Callback(SonarrMonitorShow, series_id=series_id, seasons=str(season), episodes=str(episode['id']), callback=callback),
                            title=marked + str(episode['episodeNumber']) + ". " + episode['title'],
                            summary=(episode['overview'] if 'overview' in episode else None), thumb=None))
    return oc


@route(PREFIX + '/sonarrmonitorshow')
def SonarrMonitorShow(series_id, seasons, episodes='all', locked='unlocked', callback=None):
    if not Prefs['sonarr_url'].startswith("http"):
        sonarr_url = "http://" + Prefs['sonarr_url']
    else:
        sonarr_url = Prefs['sonarr_url']
    if sonarr_url.endswith("/"):
        sonarr_url = sonarr_url[:-1]
    api_header = {
        'X-Api-Key': Prefs['sonarr_api']
    }
    try:
        show = JSON.ObjectFromURL(sonarr_url + "/api/series/" + series_id, headers=api_header)
    except Exception as e:
        Log.Debug(e.message)
        return MessageContainer(header=TITLE, message="Error retrieving Sonarr Show: " + str(series_id))
    if seasons == 'all':
        for s in show['seasons']:
            s['monitored'] = True
        data = JSON.StringFromObject(show)
        data2 = JSON.StringFromObject({'name': 'SeriesSearch', 'seriesId': int(series_id)})
        try:
            HTTP.Request(url=sonarr_url + "/api/series/", data=data, headers=api_header, method='PUT')  # Post Series to monitor
            HTTP.Request(url=sonarr_url + "/api/command", data=data2, headers=api_header)  # Search for all episodes in series
            return ManageSonarrShow(series_id=series_id, title=show['title'], locked=locked, callback=callback, message="Series sent to Sonarr")
        except Exception as e:
            Log.Debug("Sonarr Monitor failed: " + Log.Debug(Response.Status) + " - " + e.message)
            return MessageContainer("Error sending series to Sonarr")
    elif episodes == 'all':
        season_list = seasons.split()
        for s in show['seasons']:
            if str(s['seasonNumber']) in season_list:
                s['monitored'] = True
        data = JSON.StringFromObject(show)
        try:
            HTTP.Request(sonarr_url + "/api/series", data=data, headers=api_header, method='PUT')  # Post seasons to monitor
            for s in season_list:  # Search for each chosen season
                data2 = JSON.StringFromObject({'name': 'SeasonSearch', 'seriesId': int(series_id), 'seasonNumber': int(s)})
                HTTP.Request(sonarr_url + "/api/command", headers=api_header, data=data2)
            return ManageSonarrShow(series_id=series_id, locked=locked, callback=callback, message="Season(s) sent sent to Sonarr")
        except Exception as e:
            Log.Debug("Sonarr Monitor failed: " + e.message)
            return MessageContainer("Error sending season to Sonarr")
    else:
        episode_list = episodes.split()
        try:
            for e in episode_list:
                episode = JSON.ObjectFromURL(sonarr_url + "/api/Episode/" + str(e), headers=api_header)
                episode['monitored'] = True
                data = JSON.StringFromObject(episode)
                HTTP.Request(sonarr_url + "/api/Episode/" + str(e), data=data, headers=api_header, method='PUT')
            data2 = JSON.StringFromObject({'name': "EpisodeSearch", 'episodeIds': episode_list})
            HTTP.Request(sonarr_url + "/api/command", headers=api_header, data=data2)
            return ManageSonarrSeason(series_id=series_id, season=seasons, locked=locked, callback=callback, message="Episode sent to Sonarr")
        except Exception as e:
            Log.Debug("Sonarr Monitor failed: " + e.message)
            return MessageContainer("Error sending episode to Sonarr")
            # return MainMenu(locked=locked)


def ShowExists(tvdbid):
    if not Prefs['sonarr_url'].startswith("http"):
        sonarr_url = "http://" + Prefs['sonarr_url']
    else:
        sonarr_url = Prefs['sonarr_url']
    if not sonarr_url.endswith("/"):
        sonarr_url += "/"
    api_header = {
        'X-Api-Key': Prefs['sonarr_api']
    }
    series = JSON.ObjectFromURL(sonarr_url + "api/Series", headers=api_header)
    for show in series:
        if show['tvdbId'] == int(tvdbid) and show['id']:
            return show['id']
    return False


# Sickbeard Functions


@route(PREFIX + "/sendtosickbeard")
def SendToSickbeard(series_id, locked='unlocked'):
    # return ViewRequests(locked=locked, message="Sorry, Sickbeard is not available yet.")
    if not Prefs['sickbeard_url'].startswith("http"):
        sickbeard_url = "http://" + Prefs['sickbeard_url']
    else:
        sickbeard_url = Prefs['sickbeard_url']
    if not sickbeard_url.endswith("/"):
        sickbeard_url += "/"
    title = Dict['tv'][series_id]['title']
    data = dict(cmd='show.addnew', tvdbid=series_id)

    use_sickrage = (Prefs['sickbeard_fork'] == 'SickRage')

    if Prefs['sickbeard_location']:
        data['location'] = Prefs['sickbeard_location']
    if Prefs['sickbeard_status']:
        data['status'] = Prefs['sickbeard_status']
    if Prefs['sickbeard_initial']:
        data['initial'] = Prefs['sickbeard_initial']
    if Prefs['sickbeard_archive']:
        data['archive'] = Prefs['sickbeard_archive']
    if Prefs['sickbeard_language'] or use_sickrage:
        data['lang'] = Prefs['sickbeard_language'] if Prefs['sickbeard_language'] else "en"  # SickRage requires lang set

    if use_sickrage:
        data['anime'] = False  # SickRage requires anime set

    # Log.Debug(str(data))

    try:
        resp = JSON.ObjectFromURL(sickbeard_url + "api/" + Prefs['sickbeard_api'], values=data)
        # Log.Debug(JSON.StringFromObject(resp))
        if 'success' in resp and resp['success']:
            if Client.Platform in NO_MESSAGE_CONTAINER_CLIENTS or Client.Product in NO_MESSAGE_CONTAINER_CLIENTS:
                oc = ObjectContainer(title1=Prefs['sickbeard_fork'], title2="Success")
            else:
                oc = ObjectContainer(header=TITLE, message="Show added to " + Prefs['sickbeard_fork'])
            Dict['tv'][series_id]['automated'] = True
        else:
            if Client.Platform in NO_MESSAGE_CONTAINER_CLIENTS or Client.Product in NO_MESSAGE_CONTAINER_CLIENTS:
                oc = ObjectContainer(title1=Prefs['sickbeard_fork'], title2="Error")
            else:
                oc = ObjectContainer(header=TITLE, message="Could not add show to " + Prefs['sickbeard_fork'])
    except Exception as e:
        oc = ObjectContainer(header=TITLE, message="Could not add show to " + Prefs['sickbeard_fork'])
        Log.Debug(e.message)
    if checkAdmin():
        oc.add(DirectoryObject(key=Callback(ConfirmDeleteRequest, series_id=series_id, type='tv', title_year=title, locked=locked),
                               title="Delete Request"))
    oc.add(DirectoryObject(key=Callback(ViewRequests, locked=locked), title="Return to View Requests"))
    oc.add(DirectoryObject(key=Callback(MainMenu, locked=locked), title="Return to Main Menu"))
    return oc


# ManageChannel Functions

@route(PREFIX + "/managechannel")
def ManageChannel(message=None, title1=TITLE, title2="Manage Channel", locked='locked'):
    if not checkAdmin():
        return MainMenu("Only an admin can manage the channel!", locked=locked, title1="Main Menu", title2="Admin only")
    if Client.Platform in NO_MESSAGE_CONTAINER_CLIENTS or Client.Product in NO_MESSAGE_CONTAINER_CLIENTS:
        oc = ObjectContainer(title1="Manage", title2=message)
    else:
        oc = ObjectContainer(header=TITLE, message=message)
    oc.add(DirectoryObject(key=Callback(ManageUsers, locked=locked), title="Manage Users"))
    oc.add(PopupDirectoryObject(key=Callback(ResetDict, locked=locked), title="Reset Dictionary Settings"))
    oc.add(DirectoryObject(key=Callback(Changelog, locked=locked), title="Changelog"))
    oc.add(DirectoryObject(key=Callback(MainMenu, locked=locked), title="Return to Main Menu"))
    return oc


@route(PREFIX + "/manageusers")
def ManageUsers(locked='locked', message=None):
    if not checkAdmin():
        return MainMenu("Only an admin can manage the channel!", locked=locked, title1="Main Menu", title2="Admin only")
    if Client.Platform in NO_MESSAGE_CONTAINER_CLIENTS or Client.Product in NO_MESSAGE_CONTAINER_CLIENTS:
        oc = ObjectContainer(title1="Manage Users", title2=message)
    else:
        oc = ObjectContainer(header=TITLE, message=message)
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


@route(PREFIX + "/manageuser")
def ManageUser(token, locked='locked', message=None):
    if not checkAdmin():
        return MainMenu("Only an admin can manage the channel!", locked=locked, title1="Main Menu", title2="Admin only")
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
    if token in Dict['sonarr_users']:
        oc.add(DirectoryObject(key=Callback(SonarrUser, token=token, set='False', locked=locked), title="Remove Sonarr Management"))
    else:
        oc.add(DirectoryObject(key=Callback(SonarrUser, token=token, set='True', locked=locked), title="Allow Sonarr Management"))
    if token in Dict['blocked']:
        oc.add(DirectoryObject(key=Callback(BlockUser, token=token, set='False', locked=locked), title="Unblock User"))
    else:
        oc.add(DirectoryObject(key=Callback(BlockUser, token=token, set='True', locked=locked), title="Block User"))
    oc.add(PopupDirectoryObject(key=Callback(DeleteUser, token=token, locked=locked, confirmed='False'), title="Delete User"))

    oc.add(DirectoryObject(key=Callback(ManageChannel, locked=locked), title="Return to Manage Channel"))

    return oc


@route(PREFIX + "/blockuser")
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


@route(PREFIX + "/sonarruser")
def SonarrUser(token, set, locked='locked'):
    if set == 'True':
        if token in Dict['sonarr_users']:
            return ManageUser(token=token, locked=locked, message="User already in Sonarr list")
        else:
            Dict['sonarr_users'].append(token)
            return ManageUser(token=token, locked=locked, message="User is now allowed to manage Sonarr")
    elif set == 'False':
        if token in Dict['blocked']:
            Dict['sonarr_users'].remove(token)
            return ManageUser(token=token, locked=locked, message="User can no longer manage Sonarr")
    return ManageUser(token=token, locked=locked)


@route(PREFIX + "/deleteuser")
def DeleteUser(token, locked='locked', confirmed='False'):
    if not checkAdmin():
        return MainMenu("Only an admin can manage the channel!", locked=locked, title1="Main Menu", title2="Admin only")
    oc = ObjectContainer(title1="Confirm Delete User?", title2=Dict['register'][token]['nickname'])
    if confirmed == 'False':
        oc.add(DirectoryObject(key=Callback(DeleteUser, token=token, locked=locked, confirmed='True'), title="Yes"))
        oc.add(DirectoryObject(key=Callback(ManageUser, token=token, locked=locked), title="No"))
    elif confirmed == 'True':
        Dict['register'].pop(token, None)
        return ManageUsers(locked=locked, message="User registration has been deleted.")
    return oc


@route(PREFIX + "/resetdict")
def ResetDict(locked='locked', confirm='False'):
    if not checkAdmin():
        return MainMenu("Only an admin can manage the channel!", title1="Main Menu", title2="Admin only")
    if confirm == 'False':
        if Client.Platform in NO_MESSAGE_CONTAINER_CLIENTS or Client.Product in NO_MESSAGE_CONTAINER_CLIENTS:
            oc = ObjectContainer(title1="Reset Info", title2="Confirm")
        else:
            oc = ObjectContainer(header=TITLE,
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
        Dict['sonarr_users'] = []

    return ManageChannel(message="Dictionary has been reset!", locked=locked)


@route(PREFIX + "/changelog")
def Changelog(locked='locked'):
    oc = ObjectContainer(title1=TITLE, title2="Changelog")
    clog = HTTP.Request(CHANGELOG_URL)
    changes = clog.content
    changes = changes.splitlines()
    oc.add(DirectoryObject(key=Callback(Changelog, locked=locked), title="Current Version: " + str(VERSION), thumb=R('plexrequestchannel.png')))
    for change in changes[:10]:
        csplit = change.split("-")
        title = csplit[0].strip() + " - v" + csplit[1].strip()
        oc.add(DirectoryObject(key=Callback(ShowMessage, header=title, message=change), title=title, summary=csplit[2].strip(),
                               thumb=R('plexrequestchannel.png')))
    oc.add(DirectoryObject(key=Callback(ManageChannel, locked=locked), title="Return to Manage Channel", thumb=R('return.png')))
    return oc


@route(PREFIX + "/showmessage")
def ShowMessage(header, message):
    return MessageContainer(header=header, message=message)


@route(PREFIX + "/reportproblem")
def ReportProblem(locked='locked'):
    oc = ObjectContainer(title1=TITLE, title2="Report Problem")
    # oc.add(DirectoryObject(key=Callback(ReportProblemMedia, locked=locked), title="Report Problem with Media"))
    if Client.Product in DUMB_KEYBOARD_CLIENTS or Client.Platform in DUMB_KEYBOARD_CLIENTS:  # Clients in this list do not support InputDirectoryObjects
        Log.Debug("Client does not support Input. Using DumbKeyboard")
        oc.add(
            DirectoryObject(key=Callback(Keyboard, callback=ConfirmReportProblem, parent=ReportProblem, locked=locked, title="Report General Problem",
                                         message="What is the problem?"), title="Report General Problem"))
    elif Client.Product == "Plex Web":  # Plex Web does not create a popup input directory object, so use an intermediate menu
        oc.add(DirectoryObject(key=Callback(ReportGeneralProblem, locked=locked), title="Report a General Problem"))
    else:  # All other clients
        oc.add(
            InputDirectoryObject(key=Callback(ConfirmReportProblem, locked=locked), title="Report a General Problem", prompt="What is the Problem?"))
    return oc


@route(PREFIX + "/reportgeneralproblem")
def ReportGeneralProblem(locked='locked'):
    if Client.Platform in NO_MESSAGE_CONTAINER_CLIENTS or Client.Product in NO_MESSAGE_CONTAINER_CLIENTS:
        oc = ObjectContainer(title2=title)
    else:
        oc = ObjectContainer(header=TITLE, message="Please enter your problem in the search box and press enter.")
    if Client.Product in DUMB_KEYBOARD_CLIENTS or Client.Platform in DUMB_KEYBOARD_CLIENTS:
        Log.Debug("Client does not support Input. Using DumbKeyboard")
        # DumbKeyboard(prefix=PREFIX, oc=oc, callback=SearchTV, dktitle="Request a TV Show", dkthumb=R('search.png'), locked=locked)
        oc.add(DirectoryObject(key=Callback(Keyboard, callback=ConfirmReportProblem, parent=ReportProblem, locked=locked), title="Report a General Problem"))
    else:
        oc.add(
            InputDirectoryObject(key=Callback(ConfirmReportProblem, locked=locked), title="Report a General Problem", prompt="What is the problem?"))
    return oc


@route(PREFIX + "/reportproblemmedia")
def ReportProblemMedia(locked='locked'):
    oc = ObjectContainer()
    return oc


@route(PREFIX + "/confirmreportproblem")
def ConfirmReportProblem(query="", locked='locked'):
    oc = ObjectContainer(title1="Confirm", title2=query)
    oc.add(DirectoryObject(key=Callback(NotifyProblem, problem=query), title="Yes", thumb=R('check.png')))
    oc.add(DirectoryObject(key=Callback(MainMenu, locked=locked), title="No", thumb=R('x-mark.png')))
    return oc


@route(PREFIX + "/notifyproblem")
def NotifyProblem(problem, locked='locked', rating_key="", path=""):
    title = "Plex Request Channel - Problem Reported"
    user = "A user"
    token = Request.Headers['X-Plex-Token']
    if token in Dict['register'] and Dict['register'][token]['nickname']:
        user = Dict['register'][token]['nickname']
    body = user + " has reported a problem with the Plex Server. \n" + \
           "Issue: " + problem
    Notify(title=title, body=body, devices=Prefs['pushbullet_devices'])
    return MainMenu(locked=locked, message="The admin will be notified", title1="Main Menu", title2="Admin notified of problem")


# Notifications Functions

# Notify user of requests
def notifyRequest(req_id, req_type, title="", message=""):
    if Prefs['pushbullet_api']:
        try:
            user = "A user"
            token = Request.Headers['X-Plex-Token']
            if token in Dict['register'] and Dict['register'][token]['nickname']:
                user = Dict['register'][token]['nickname']
            if req_type == 'movie':
                movie = Dict['movie'][req_id]
                title_year = movie['title'] + " (" + movie['year'] + ")"
                title = "Plex Request Channel - New Movie Request"
                message = user + " has requested a new movie.\n" + title_year + "\nIMDB id: " + req_id + "\nPoster: " + movie['poster']
            elif req_type == 'tv':
                tv = Dict['tv'][req_id]
                title = "Plex Request Channel - New TV Show Request"
                message = user + " has requested a new tv show.\n" + tv['title'] + "\nTVDB id: " + req_id + "\nPoster: " + tv['poster']
            else:
                return
            if Prefs['pushbullet_devices']:
                devices = Prefs['pushbullet_devices'].split(",")
                for d in devices:
                    response = sendPushBullet(title, message, d)
                    if response:
                        Log.Debug("Pushbullet notification sent to device: " + d + " for: " + req_id)
            else:
                response = sendPushBullet(title, message)
                if response:
                    Log.Debug("Pushbullet notification sent for: " + req_id)
        except Exception as e:
            Log.Debug("Pushbullet failed: " + e.message)
    if Prefs['pushover_user']:
        try:
            user = "A user"
            token = Request.Headers['X-Plex-Token']
            if token in Dict['register'] and Dict['register'][token]['nickname']:
                user = Dict['register'][token]['nickname']
            if req_type == 'movie':
                movie = Dict['movie'][req_id]
                title_year = movie['title'] + " (" + movie['year'] + ")"
                title = "Plex Request Channel - New Movie Request"
                message = user + " has requested a new movie.\n" + title_year + "\nIMDB id: " + req_id + "\nPoster: " + movie['poster']
            elif req_type == 'tv':
                tv = Dict['tv'][req_id]
                title = "Plex Request Channel - New TV Show Request"
                message = user + " has requested a new tv show.\n" + tv['title'] + "\nTVDB id: " + req_id + "\nPoster: " + tv['poster']
            else:
                return
            response = sendPushover(title, message)
            if response:
                Log.Debug("Pushover notification sent for :" + req_id)
        except Exception as e:
            Log.Debug("Pushover failed: " + e.message)
    if Prefs['email_to']:
        try:
            user = "A user"
            token = Request.Headers['X-Plex-Token']
            if token in Dict['register'] and Dict['register'][token]['nickname']:
                user = Dict['register'][token]['nickname']
            if req_type == 'movie':
                movie = Dict['movie'][req_id]
                title = movie['title'] + " (" + movie['year'] + ")"
                poster = movie['poster']
                id_type = "IMDB"
                subject = "Plex Request Channel - New Movie Request"
                summary = ""
                if movie['summary']:
                    summary = movie['summary'] + "<br>\n"
            elif req_type == 'tv':
                tv = Dict['tv'][req_id]
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
                      "(" + id_type + " id: " + req_id + ") <br>\n" + \
                      summary + \
                      "<Poster:><img src= '" + poster + "' width='300'>"
            sendEmail(subject, message, 'html')
            Log.Debug("Email notification sent for: " + req_id)
        except Exception as e:
            Log.Debug("Email failed: " + e.message)


def Notify(title, body, devices=None):
    if Prefs['email_to']:
        try:
            if not sendEmail(title, body, 'html'):
                Log.Debug("Email notification sent")
        except Exception as e:
            Log.Debug("Email failed: " + e.message)
    if Prefs['pushbullet_api']:
        try:
            if devices:
                for d in devices.split(','):
                    if sendPushBullet(title, body, d):
                        Log.Debug("Pushbullet notification sent to " + d)
            elif sendPushBullet(title, body):
                Log.Debug("Pushbullet notification sent")
        except Exception as e:
            Log.Debug("PushBullet failed: " + e.message)
    if Prefs['pushover_user']:
        try:
            if sendPushover(title, body):
                Log.Debug("Pushover notification sent")
        except Exception as e:
            Log.Debug("Pushover failed: " + e.message)


def sendPushBullet(title, body, device_iden=""):
    api_header = {'Authorization': 'Bearer ' + Prefs['pushbullet_api'],
                  'Content-Type': 'application/json'
                  }
    data = {'type': 'note', 'title': title, 'body': body}
    if device_iden:
        data['device_iden'] = device_iden
    values = JSON.StringFromObject(data)
    return HTTP.Request(PUSHBULLET_API_URL + "pushes", data=values, headers=api_header)


def sendPushover(title, message):
    data = {'token': Prefs['pushover_api'], 'user': Prefs['pushover_user'], 'title': title, 'message': message}
    return HTTP.Request(PUSHOVER_API_URL, values=data)


# noinspection PyUnresolvedReferences
def sendEmail(subject, body, email_type='html'):
    from email.MIMEText import MIMEText
    from email.MIMEMultipart import MIMEMultipart
    import smtplib

    msg = MIMEMultipart()
    msg['From'] = Prefs['email_from']
    msg['To'] = Prefs['email_to']
    msg['Subject'] = subject
    msg.attach(MIMEText(body, email_type))
    server = smtplib.SMTP(Prefs['email_server'], int(Prefs['email_port']))
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(Prefs['email_username'], Prefs['email_password'])
    text = msg.as_string()
    senders = server.sendmail(Prefs['email_from'], Prefs['email_to'], text)
    server.quit()
    return senders


"""
List of Client.Product and Client.Platform

Client.Product 	        Description
--------------          ------------------------------------------------------------------
Plex for Android 	    Android phone
Plex for iOS 	        Apple phone
Plex Home Theater 	    This is for Plex Home Theater
Plex Media Player 	    This is for new Plex Media Player
Plex Web 	            Plex Web client, from web browser
Plex for Firefox TV 	Plex Firefox TV, (source), this one is a guess
Plex for Roku 	        Roku
OpenPHT 	            OpenPHT
Plex Chromecast 	    Chromecast
NotifyPlex 	            NZBGet
HTPC Manager 	        Windows Server (Windows-2012Server-6.2.9200). Not sure if correct.
Plex for Xbox One 	    Xbox One
Plex for Xbox 360       Xbox 360
Plex for Samsung        Samsung

Client.Platform 	    Description
---------------         -------------------------------------------------------------------
Android 	            Android phone
iOS 	                Apple phone
Safari 	                This is a guess from looking at a Service URL code.
Chrome              	Plex Web client on Chrome internet browser
Plex Home Theater 	    This is for Plex Home Theater
Konvergo 	            Plex Media Player, (running on a Raspberry PI 2 B)
tvOS 	                New AppleTV
MacOSX 	                MacOSX
Linux 	                Linux
Windows 	            Windows
LGTV 	                LGTV
Roku 	                Roku
Chromecast          	Chromecast
NZBGet 	                NZBGet
Xbox One            	Xbox One
Xbox 360                Xbox 360
Samsung                 Samsung
"""
