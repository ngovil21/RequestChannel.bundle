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

### URL Constants for OpenMovieDataBase ###############
OMDB_API_URL = "http://www.omdbapi.com/"
#######################################################


def Start():
    ObjectContainer.title1 = TITLE
    ObjectContainer.art = R(ART)

    DirectoryObject.thumb = R(ICON)
    DirectoryObject.art = R(ART)
    EpisodeObject.thumb = R(ICON)
    EpisodeObject.art = R(ART)
    VideoClipObject.thumb = R(ICON)
    VideoClipObject.art = R(ART)

    # If no Requests file exists, create it
    # The request file will be where user requests will be stored
    Dict.Reset()

###################################################################################################
# This tells Plex how to list you in the available channels and what type of channels this is
@handler(PREFIX, TITLE, art=ART, thumb=ICON)
def MainMenu():
    oc = ObjectContainer(replace_parent=True)

    oc.add(DirectoryObject(key=Callback(AddNewMovie, title="Request a Movie"), title="Request a Movie"))
    oc.add(DirectoryObject(key=Callback(AddNewTVShow, title="Request a TV Show"), title="Request a TV Show"))
    if Prefs['password']:
        oc.add(InputDirectoryObject(key=Callback(ViewRequestsPassword, title="View Requests"), title="View Requests"))
    else:
        oc.add(DirectoryObject(key=Callback(ViewRequests, title="View Requests"), title="View Requests"))

    return oc


@route(PREFIX + '/addnewmovie')
def AddNewMovie(title):
    oc = ObjectContainer()

    oc.add(InputDirectoryObject(key=Callback(SearchMovie, title="Search Results"), title=title, prompt="Enter the name or IMDB id of the movie:"))
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
        #Log.Debug(JSON.StringFromObject(request))
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
                oc.add(DirectoryObject(key=Callback(ConfirmMovieRequest, id=key['id'], title=key['title'], year=year, poster=thumb, backdrop=art, summary=key['overview']), title=title_year, thumb=thumb, summary=key['overview'], art=art))
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
                oc.add(DirectoryObject(key=Callback(ConfirmMovieRequest, id=key['imdbID'], title=key['Title'], year=key['Year'], poster=key['Poster']), title=title_year, thumb=key['Poster']))

        else:
            Log.Debug("No Results Found")
            return ObjectContainer(header=TITLE, message="Sorry there were no results found for your search.")
    return oc


@route(PREFIX + '/confirmmovierequest')
def ConfirmMovieRequest(id, title, year="", poster="", backdrop="", summary=""):
    title_year = title + " " + "(" + year + ")"
    oc = ObjectContainer(title1="Confirm Movie Request", title2="Are you sure you would like to request the movie " + title_year + "?")

    oc.add(DirectoryObject(key=Callback(AddMovieRequest, id=id, title=title, year=year, poster=poster, backdrop=backdrop, summary=summary), title="Yes"))
    oc.add(DirectoryObject(key=Callback(MainMenu), title="No"))

    return oc


@route(PREFIX + '/addmovierequest')
def AddMovieRequest(id, title, year="", poster="", backdrop="", summary=""):

    if id in Dict:
        Log.Debug("Movie is already requested")
        return ObjectContainer(header=TITLE, message="Movie has already been requested.")
    else:
        Dict[id] = {'title':title, 'year':year, 'poster':poster, 'backdrop':backdrop, 'summary':summary}
        Dict.Save()
        return ObjectContainer(header=TITLE, message="Movie has been requested.")


@route(PREFIX + '/addtvshow')
def AddNewTVShow(title):
    oc = ObjectContainer()
    return oc


@route(PREFIX + '/viewrequests')
def ViewRequests(title):
    oc = ObjectContainer()
    if not Dict:
        Log.Debug("There are no requests")
        oc = ObjecContainer(header=TITLE,message="There are currently no requests.")
        oc.add(DirectoryObject(key=Callback(MainMenu), title="Return to Main Menu"))
    for movie_id in Dict:
        key = Dict[movie_id]
        title_year = key['title'] + " (" + key['year'] + ")"
        oc.add(DirectoryObject(key=Callback(ViewMovieRequest, key=key), title=title_year, thumb=key['poster'], summary=key['summary'], art=key['backdrop']))
    if len(oc)==0:
        return ObjectContainer()
    return oc

def ViewRequestsPassword(title,query):
    if query == Prefs['password']:
        oc = ObjectContainer(header=TITLE, message="Password is correct!")
        oc.add(DirectoryObject(key=Callback(ViewRequests, title="View Requests"), title="Continue to View Requests"))
    else:
        oc = ObjectContainer(header=TITLE, message="Password is incorrect!")
        oc.add(DirectoryObject(key=Callback(MainMenu), title="Back to Main Menu"))

    return oc

@route(PREFIX + '/viewmovierequest')
def ViewMovieRequest(key):
    oc = ObjectContainer()

    return oc