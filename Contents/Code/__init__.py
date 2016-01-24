TITLE = 'Plex Request Channel'
PREFIX = '/video/plexrequestchannel'

ART = 'art-default.jpg'
ICON = 'icon-default.png'

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


#######################################################
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

    # Dict.Reset()


###################################################################################################
# This tells Plex how to list you in the available channels and what type of channels this is
@handler(PREFIX, TITLE, art=ART, thumb=ICON)
def MainMenu():
    oc = ObjectContainer(replace_parent=True)

    oc.add(DirectoryObject(key=Callback(AddNewMovie, title="Request a Movie"), title="Request a Movie"))
    oc.add(DirectoryObject(key=Callback(AddNewTVShow, title="Request a TV Show"), title="Request a TV Show"))
    if Prefs['password'] == None or Prefs['password'] == "":
        oc.add(DirectoryObject(key=Callback(ViewRequests), title="View Requests"))
    else:
        oc.add(InputDirectoryObject(key=Callback(ViewRequestsPassword), title="View Requests",
                                    prompt="Please enter the password:"))

    return oc


@route(PREFIX + '/addnewmovie')
def AddNewMovie(title):
    oc = ObjectContainer()

    oc.add(InputDirectoryObject(key=Callback(SearchMovie, title="Search Results"), title=title, prompt="Enter the name of the movie:"))
    return oc


@route(PREFIX + '/searchmovie')
def SearchMovie(title, query):
    oc = ObjectContainer(title1=title)
    query = String.Quote(query, usePlus=True)
    if Prefs['movie_db'] == "TheMovieDatabase":
        headers = {
            'Accept': 'application/json'
        }
        request = JSON.ObjectFromURL(url=TMDB_API_URL + "search/movie?api_key=" + TMDB_API_KEY + "&query=" + query, headers=headers)
        # Log.Debug(JSON.StringFromObject(request))
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
                oc.add(DirectoryObject(key=Callback(ConfirmMovieRequest, id=key['id'], title=key['title'], year=year, poster=thumb, backdrop=art,
                                                    summary=key['overview']), title=title_year, thumb=thumb, summary=key['overview'], art=art))
            else:
                Log.Debug("No Results Found")
                return ObjectContainer(header=TITLE, message="Sorry there were no results found for your search.")
    else:  # Use OMDB By Default
        request = JSON.ObjectFromURL(url=OMDB_API_URL + "?s=" + query + "&r=json")
        if 'Search' in request:
            results = request['Search']
            for key in results:
                if not key['Title']:
                    continue
                title_year = key['Title'] + " (" + key['Year'] + ")"
                oc.add(
                    DirectoryObject(key=Callback(ConfirmMovieRequest, id=key['imdbID'], title=key['Title'], year=key['Year'], poster=key['Poster']),
                                    title=title_year, thumb=key['Poster']))

        else:
            Log.Debug("No Results Found")
            oc = ObjectContainer(header=TITLE, message="Sorry there were no results found for your search.")
            oc.add(InputDirectoryObject(key=Callback(SearchMovie, title="Search Results"), title="Search Again",
                                        prompt="Enter the name of the movie:"))
            oc.add(DirectoryObject(key=Callback(MainMenu), title="Back to Main Menu"))
            return oc
    return oc


@route(PREFIX + '/confirmmovierequest')
def ConfirmMovieRequest(id, title, year="", poster="", backdrop="", summary=""):
    title_year = title + " " + "(" + year + ")"
    oc = ObjectContainer(title1="Confirm Movie Request", title2="Are you sure you would like to request the movie " + title_year + "?")

    oc.add(
        DirectoryObject(key=Callback(AddMovieRequest, id=id, title=title, year=year, poster=poster, backdrop=backdrop, summary=summary), title="Yes"))
    oc.add(DirectoryObject(key=Callback(MainMenu), title="No"))

    return oc


@route(PREFIX + '/addmovierequest')
def AddMovieRequest(id, title, year="", poster="", backdrop="", summary=""):
    if id in Dict:
        Log.Debug("Movie is already requested")
        return ObjectContainer(header=TITLE, message="Movie has already been requested.")
    else:
        Dict[id] = {'type': 'movie', 'id': id, 'title': title, 'year': year, 'poster': poster, 'backdrop': backdrop, 'summary': summary}
        Dict.Save()
        oc = ObjectContainer(header=TITLE, message="Movie has been requested.")
        oc.add(DirectoryObject(key=Callback(MainMenu), title="Return to Main Menu"))

        return oc


@route(PREFIX + '/addtvshow')
def AddNewTVShow(title):
    oc = ObjectContainer()

    oc.add(InputDirectoryObject(key=Callback(SearchTV), title="Request a TV Show", prompt="Enter the name of the TV Show:"))
    return oc


@route(PREFIX + '/searchtv')
def SearchTV(query):
    oc = ObjectContainer(title1="Search Results")
    query = String.Quote(query, usePlus=True)
    xml = XML.ElementFromURL(TVDB_API_URL + "GetSeries.php?seriesname=" + query)
    series = xml.xpath("//Series")
    if len(series) == 0:
        oc = ObjectContainer(header=TITLE, message="Sorry there were no results found.")
        oc.add(InputDirectoryObject(key=Callback(SearchTV), title="Search Again", prompt="Enter the name of the TV Show:"))
        oc.add(DirectoryObject(key=Callback(MainMenu), title="Return to Main Menu"))
        return oc
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
            elif child.tag.lower() == "banner" and child.text:
                poster = TVDB_BANNER_URL + child.text
            elif child.tag.lower() == "overview" and child.text:
                summary = child.text
            elif child.tag.lower() == "firstaired" and child.text:
                release_date = child.text
                year = release_date[0:4]
        if id == "":
            Log.Debug("No id found!")
        if year:
            title_year = title + " (" + year + ")"
        else:
            title_year = title

        # serieid = serie.find("seriesid")
        # if serieid
        # if serieid and serieid.text:
        #     id = serieid.text
        # else:
        #     Log.Debug("No id found!")
        #     id = ""
        # seriename = serie.find("seriesname")
        # if seriename and seriename.text:
        #     title = seriename.text
        #     title_year = title
        # else:
        #     title = ""
        #     title_year = ""
        #     Log.Debug("No title found!")
        # banner = serie.find("banner")
        # if banner and banner.text:
        #     poster = TVDB_BANNER_URL + banner.text
        # else:
        #     poster=""
        # overiew = serie.find("Overview")
        # if overiew and overiew.text:
        #     summary = overiew.text
        # else:
        #     summary = ""
        # firstaired = serie.find("FirstAired")
        # if firstaired and firstaired.text:
        #     release_date = firstaired.text
        #     year = release_date[0:4]
        #     title_year = title + " (" + year + ")"
        # else:
        #     release_date = ""
        #     year = ""

        oc.add(DirectoryObject(key=Callback(ConfirmTVRequest, id=id, title=title, year=year, poster=poster, summary=summary), title=title_year,
                               thumb=poster))

    return oc


@route(PREFIX + '/confirmtvrequest')
def ConfirmTVRequest(id, title, year="", poster="", backdrop="", summary=""):
    if year:
        title_year = title + " " + "(" + year + ")"
    else:
        title_year = title
    oc = ObjectContainer(title1="Confirm TV Request", title2="Are you sure you would like to request the TV Show " + title_year + "?")

    oc.add(DirectoryObject(key=Callback(AddTVRequest, id=id, title=title, year=year, poster=poster, backdrop=backdrop, summary=summary), title="Yes"))
    oc.add(DirectoryObject(key=Callback(MainMenu), title="No"))

    return oc


@route(PREFIX + '/addtvrequest')
def AddTVRequest(id, title, year="", poster="", backdrop="", summary=""):
    if id in Dict:
        Log.Debug("TV Show is already requested")
        return ObjectContainer(header=TITLE, message="TV Show has already been requested.")
    else:
        Dict[id] = {'type': 'tv', 'id': id, 'title': title, 'year': year, 'poster': poster, 'backdrop': backdrop, 'summary': summary}
        Dict.Save()
        oc = ObjectContainer(header=TITLE, message="TV Show has been requested.")
        oc.add(DirectoryObject(key=Callback(MainMenu), title="Return to Main Menu"))

        return oc


@route(PREFIX + '/viewrequests')
def ViewRequests():
    oc = ObjectContainer()
    if not Dict:
        Log.Debug("There are no requests")
        oc = ObjectContainer(header=TITLE, message="There are currently no requests.")
        oc.add(DirectoryObject(key=Callback(MainMenu), title="Return to Main Menu"))
    else:
        for id in Dict:
            key = Dict[id]
            title_year = key['title'] + " (" + key['year'] + ")"
            oc.add(DirectoryObject(key=Callback(ViewRequest, id=id), title=title_year, thumb=key['poster'], summary=key['summary'],
                                   art=key['backdrop']))
    return oc


@route(PREFIX + '/viewrequestspassword')
def ViewRequestsPassword(query):
    if query == Prefs['password']:
        oc = ObjectContainer(header=TITLE, message="Password is correct!")
        oc.add(DirectoryObject(key=Callback(ViewRequests), title="Continue to View Requests"))
    else:
        oc = ObjectContainer(header=TITLE, message="Password is incorrect!")
        oc.add(DirectoryObject(key=Callback(MainMenu), title="Back to Main Menu"))

    return oc


@route(PREFIX + '/viewrequest')
def ViewRequest(id):
    key = Dict[id]
    title_year = key['title'] + " (" + key['year'] + ")"
    oc = ObjectContainer(title2=title_year)
    oc.add(DirectoryObject(key=Callback(ConfirmDeleteRequest, id=id, title_year=title_year), title="Delete Request"))
    if key['type'] == 'movie':
        if Prefs['couchpotato_url'] and Prefs['couchpotato_api']:
            oc.add(DirectoryObject(key=Callback(SendToCouchpotato, id=id), title="Send to CouchPotato"))
    if key['type'] == 'tv':
        if Prefs['sonarr_url'] and Prefs['sonarr_api']:
            oc.add(DirectoryObject(key=Callback(SendToSonarr, id=id), title="Send to Sonarr"))

    return oc


@route(PREFIX + '/confirmdeleterequest')
def ConfirmDeleteRequest(id, title_year=""):
    oc = ObjectContainer(title2="Are you sure you would like to delete the request for " + title_year + "?")
    oc.add(DirectoryObject(key=Callback(DeleteRequest, id=id), title="Yes"))
    oc.add(DirectoryObject(key=Callback(ViewRequests), title="No"))
    return oc


def DeleteRequest(id):
    oc = ObjectContainer(header=TITLE, message="Request was deleted!")
    if id in Dict:
        del Dict[id]
    Dict.Save()
    oc.add(DirectoryObject(key=Callback(ViewRequests), title="Return to View Requests"))
    return oc


@route(PREFIX + '/sendtocouchpotato')
def SendToCouchpotato(id):
    if not id.startswith("tt"):  # Check if id is an imdb id
        # we need to convert tmdb id to imdb
        json = JSON.ObjectFromURL(TMDB_API_URL + "movie/id/?api_key=" + TMDB_API_KEY, headers={'Accept': 'application/json'})
        if 'imdb_id' in json and json['imdb_id']:
            imdb_id = json['imdb_id']
        else:
            oc = ObjectContainer(header=TITLE, message="Unable to get IMDB id for movie, add failed...")
            oc.add(DirectoryObject(key=Callback(ViewRequests), title="Return to View Requests"))
            return oc
    else:
        imdb_id = id
    # we have an imdb id, add to couchpotato
    if not Prefs['couchpotato_url'].startswith("http"):
        couchpotato_url = "http://" + Prefs['couchpotato_url']
    else:
        couchpotato_url = Prefs['couchpotato_url']
    if not couchpotato_url.endswith("/"):
        couchpotato_url = couchpotato_url + "/"
    request_url = couchpotato_url + "api/" + Prefs['couchpotato_api'] + "/movie.add/?identifier=" + imdb_id
    Log.Debug(request_url)
    json = JSON.ObjectFromURL(request_url)
    if 'success' in json and json['success']:
        oc = ObjectContainer(header=TITLE, message="Movie Request Sent to CouchPotato!")
    else:
        oc = ObjectContainer(header=TITLE, message="Movie Request failed!")
    key = Dict[id]
    title_year = key['title'] + " (" + key['year'] + ")"
    oc.add(DirectoryObject(key=Callback(ConfirmDeleteRequest, id=id, title_year=title_year), title="Delete Request"))
    oc.add(DirectoryObject(key=Callback(ViewRequests), title="Return to View Requests"))
    return oc


@route(PREFIX + '/sendtosonarr')
def SendToSonarr(id):
    oc = ObjectContainer()
    return oc
