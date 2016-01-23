TITLE = 'Plex Request Channel'
PREFIX = '/video/plexrequestchannel'

ART = 'art-default.jpg'
ICON = 'icon-default.png'

DATA_FILE = "Requests"

TMDB_API_KEY = "096c49df1d0974ee573f0295acb9e3ce"
TMDB_API_URL = "http://api.themoviedb.org/3/"
TMDB_IMAGE_BASE_URL = "http://image.tmdb.org/t/p/"
POSTER_SIZE = "w500/"
BACKDROP_SIZE = "original/"


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
    if not Data.Exists(DATA_FILE):
        json = JSON.Element(DATA_FILE)
        Data.SaveObject(DATA_FILE, json)


###################################################################################################
# This tells Plex how to list you in the available channels and what type of channels this is 
@handler(PREFIX, TITLE, art=ART, thumb=ICON)
def MainMenu():
    oc = ObjectContainer(replace_parent=True)

    oc.add(DirectoryObject(key=Callback(AddNewMovie, title="Request a Movie"), title="Request a Movie"))
    oc.add(DirectoryObject(key=Callback(AddNewTVShow, title="Request a TV Show"), title="Request a TV Show"))
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
    headers = {
        'Accept': 'application/json'
    }
    request = JSON.ObjectFromURL(url=TMDB_API_URL + "search/movie?api_key=" + TMDB_API_KEY + "&query=" + query, headers=headers)
    Log.Debug(JSON.StringFromObject(request))
    results = request['results']
    for key in results:
        if not key['title']:
            continue
        if key['release_date']:
            release_year = "(" + key['release_date'][0:4] + ")"
        else:
            release_year = ""
        if key['poster_path']:
            thumb = TMDB_IMAGE_BASE_URL + POSTER_SIZE + key['poster_path']
        else:
            thumb = None
        if key['backdrop_path']:
            art = TMDB_IMAGE_BASE_URL + BACKDROP_SIZE + key['backdrop_path']
        else:
            art = None
        title_year = key['title'] + " " + release_year
        oc.add(DirectoryObject(key=Callback(ConfirmMovieRequest, id=key['id'], title=key['title'], release_date=key['release_date'], poster=thumb, backdrop=art, summary=key['overview']), title=title_year, thumb=thumb, summary=key['overview'], art=art))
    return oc


@route(PREFIX + '/confirmmovierequest')
def ConfirmMovieRequest(id, title, release_date, poster, backdrop, summary):
    title_year = title + " " + "(" + release_date[0:4] + ")"
    oc = ObjectContainer(title1="Confirm Movie Request", title2="Are you sure you would like to request the movie " + title_year + "?")

    oc.add(DirectoryObject(key=Callback(AddMovieRequest, id=id, title=title, release_date=release_date, poster=poster, backdrop=backdrop, summary=summary), title="Yes"))
    oc.add(DirectoryObject(key=Callback(MainMenu), title="No"))

    return oc


@route(PREFIX + '/addmovierequest')
def AddMovieRequest(id, title, release_date, poster, backdrop, summary):
    oc = ObjectContainer()

    if Data.Exists(DATA_FILE):
        json = Data.LoadObject(DATA_FILE)
        if id in json:
            print("Movie is already requested")
        else:
            json = Data.LoadObject(DATA_FILE)
            json[id] = {'title':title, 'release_date':release_date, 'poster':poster, 'backdrop':backdrop, 'summary':summary}
            Data.SaveObject(DATA_FILE, json)

    return oc


@route(PREFIX + '/addtvshow')
def AddNewTVShow(title):
    oc = ObjectContainer()
    return oc


@route(PREFIX + '/viewrequests')
def ViewRequests(title):
    oc = ObjectContainer()
    if Data.Exists(DATA_FILE):
        Log.Debug("The file exists")
    else:
        Log.Debug("Data file does not exist!")
    json = Data.LoadObject(DATA_FILE)
    Log.Debug(JSON.StringFromObject(json))
    if not json:
        return oc
    for movie_id in sorted(json):
        key = json[movie_id]
        if not key['title']:
            key['title'] = "TMDB ID: " + movie_id
        if key['release_date']:
            release_year = "(" + key['release_date'][0:4] + ")"
        else:
            release_year = ""
        if key['poster_path']:
            thumb = TMDB_IMAGE_BASE_URL + POSTER_SIZE + key['poster_path']
        else:
            thumb = None
        if key['backdrop_path']:
            art = TMDB_IMAGE_BASE_URL + BACKDROP_SIZE + key['backdrop_path']
        else:
            art = None
        title_year = key['title'] + " " + release_year
        oc.add(DirectoryObject(key=Callback(ViewmMovieRequest, key=key), title=title_year, thumb=thumb, summary=key['overview'], art=art))

    return oc


@route(PREFIX + '/viewmovierequest')
def ViewMovieRequest(key):
    oc = ObjectContainer()

    return oc