#Movie Functions
import Channel
from Keyboard import Keyboard, DUMB_KEYBOARD_CLIENTS, NO_MESSAGE_CONTAINER_CLIENTS
from CouchPotato import SendToCouchpotato
from Notifications import notifyRequest

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


@route(Channel.PREFIX + '/addnewmovie')
def AddNewMovie(title="Request a Movie", locked='unlocked'):
    oc = ObjectContainer(header=Channel.TITLE, message="Please enter the movie name in the searchbox and press enter.")
    if Client.Platform in NO_MESSAGE_CONTAINER_CLIENTS or Client.Product in NO_MESSAGE_CONTAINER_CLIENTS:
        oc.message = None
    if Client.Product in DUMB_KEYBOARD_CLIENTS or Client.Platform in DUMB_KEYBOARD_CLIENTS:
        Log.Debug("Client does not support Input. Using DumbKeyboard")
        # oc.add(DirectoryObject(key="", title=""))
        # DumbKeyboard(prefix=PREFIX, oc=oc, callback=SearchMovie, dktitle=title, dkthumb=R('search.png'), locked=locked)
        oc.add(DirectoryObject(key=Callback(Keyboard, callback=SearchMovie, parent=Channel.CMainMenu, locked=locked), title=title, thumb=R('search.png')))
    else:
        oc.add(
            InputDirectoryObject(key=Callback(SearchMovie, locked=locked), title=title, prompt="Enter the name of the movie:", thumb=R('search.png')))
    return oc


@route(Channel.PREFIX + '/searchmovie')
def SearchMovie(title="Search Results", query="", locked='unlocked'):
    oc = ObjectContainer(title1=title, title2=query, content=ContainerContent.Shows, view_group="Details")
    query = String.Quote(query, usePlus=True)
    token = Request.Headers['X-Plex-Token']
    if Prefs['weekly_limit'] and int(Prefs['weekly_limit']) > 0 and not checkAdmin():

        if Dict['register'].get(token, None) and Dict['register'][token]['requests'] >= int(Prefs['weekly_limit']):
            return Channel.CMainMenu(message="Sorry you have reached your weekly request limit of " + Prefs['weekly_limit'] + ".", locked=locked,
                            title1="Main Menu", title2="Weekly Limit")
    if token in Dict['blocked']:
        return Channel.CMainMenu(message="Sorry you have been blocked.", locked=locked,
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
                oc = ObjectContainer(header=Channel.TITLE, message="Sorry there were no results found for your search.")
            Log.Debug("No Results Found")
            if Client.Product in DUMB_KEYBOARD_CLIENTS or Client.Platform in DUMB_KEYBOARD_CLIENTS:
                Log.Debug("Client does not support Input. Using DumbKeyboard")
                # oc.add(DirectoryObject(key="", title=""))
                # DumbKeyboard(prefix=PREFIX, oc=oc, callback=SearchMovie, dktitle="Search Again", dkthumb=R('search.png'), locked=locked)
                oc.add(DirectoryObject(key=Callback(Keyboard, callback=SearchMovie, parent=Channel.CMainMenu, locked=locked), title="Search Again",
                                       thumb=R('search.png')))
            else:
                oc.add(InputDirectoryObject(key=Callback(SearchMovie, locked=locked), title="Search Again",
                                            prompt="Enter the name of the movie:"))
            oc.add(DirectoryObject(key=Callback(Channel.CMainMenu, locked=locked), title="Back to Main Menu", thumb=R('return.png')))
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
                oc = ObjectContainer(header=Channel.TITLE, message="Sorry there were no results found for your search.")
            if Client.Product in DUMB_KEYBOARD_CLIENTS or Client.Platform in DUMB_KEYBOARD_CLIENTS:
                Log.Debug("Client does not support Input. Using DumbKeyboard")
                # DumbKeyboard(prefix=PREFIX, oc=oc, callback=SearchMovie, dktitle="Search Again", dkthumb=R('search.png'), locked=locked)
                oc.add(DirectoryObject(key=Callback(Keyboard, callback=SearchMovie, parent=Channel.CMainMenu, locked=locked), title="Search Again",
                                       thumb=R('search.png')))
            else:
                oc.add(InputDirectoryObject(key=Callback(SearchMovie, locked=locked), title="Search Again",
                                            prompt="Enter the name of the movie:"))
            oc.add(DirectoryObject(key=Callback(Channel.CMainMenu, locked=locked), title="Back to Main Menu", thumb=R('return.png')))
            return oc
    if Client.Product in DUMB_KEYBOARD_CLIENTS or Client.Platform in DUMB_KEYBOARD_CLIENTS:
        Log.Debug("Client does not support Input. Using DumbKeyboard")
        # DumbKeyboard(prefix=PREFIX, oc=oc, callback=SearchMovie, dktitle="Search Again", dkthumb=R('search.png'), locked=locked)
        oc.add(DirectoryObject(key=Callback(Keyboard, callback=SearchMovie, parent=Channel.CMainMenu, locked=locked), title="Search Again",
                               thumb=R('search.png')))
    else:
        oc.add(InputDirectoryObject(key=Callback(SearchMovie, locked=locked), title="Search Again",
                                    prompt="Enter the name of the movie:", thumb=R('search.png')))
    oc.add(DirectoryObject(key=Callback(Channel.CMainMenu, locked=locked), title="Return to Main Menu", thumb=R('return.png')))
    return oc


@route(Channel.PREFIX + '/confirmmovierequest')
def ConfirmMovieRequest(movie_id, title, source='', year="", poster="", backdrop="", summary="", locked='unlocked'):
    title_year = title + " " + "(" + year + ")"
    if Client.Platform in NO_MESSAGE_CONTAINER_CLIENTS or Client.Product in NO_MESSAGE_CONTAINER_CLIENTS:
        oc = ObjectContainer(title1="Confirm Movie Request", title2=title_year + "?")
    else:
        oc = ObjectContainer(title1="Confirm Movie Request", title2=title_year + "?",
                             header=Channel.TITLE, message="Request movie " + title_year + "?")
    found_match = False
    try:
        local_search = XML.ElementFromURL(url="http://127.0.0.1:32400/search?local=1&query=" + String.Quote(title), headers=Request.Headers)
        if local_search:
            # Log.Debug(XML.StringFromElement(local_search))
            videos = local_search.xpath("//Video")
            for video in videos:
                if video.attrib['title'] == title and video.attrib['year'] == year and video.attrib['type'] == 'movie':
                    Log.Debug("Possible match found: " + str(video.attrib['ratingKey']))
                    summary = "(In Library: " + video.attrib['librarySectionTitle'] + ") " + (video.attrib['summary'] if video.attrib['summary'] else "")
                    oc.add(TVShowObject(key=Callback(Channel.CMainMenu, locked=locked, message="Movie already in library.", title1="In Library", title2=title),
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
    if not found_match and Client.Platform == ClientPlatform.Android:  # If an android, add an empty first item because it gets truncated for some reason
        oc.add(DirectoryObject(key=None, title=""))
    oc.add(DirectoryObject(
        key=Callback(AddMovieRequest, movie_id=movie_id, source=source, title=title, year=year, poster=poster, backdrop=backdrop, summary=summary,
                     locked=locked), title="Add Anyways" if found_match else "Yes", thumb=R('check.png')))
    # if Client.Platform == ClientPlatform.Android:  # If an android, add an empty first item because it gets truncated for some reason
    #     oc.add(DirectoryObject(key=None, title=""))
    oc.add(DirectoryObject(key=Callback(Channel.CMainMenu, locked=locked), title="No", thumb=R('x-mark.png')))

    return oc

@route(Channel.PREFIX + '/addmovierequest')
def AddMovieRequest(movie_id, title, source='', year="", poster="", backdrop="", summary="", locked='unlocked'):
    if movie_id in Dict['movie']:
        Log.Debug("Movie is already requested")
        return Channel.CMainMenu(locked=locked, message="Movie has already been requested", title1=title, title2="Already Requested")
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
        return Channel.CMainMenu(locked=locked, message="Movie has been requested", title1="Main Menu", title2="Movie Requested")