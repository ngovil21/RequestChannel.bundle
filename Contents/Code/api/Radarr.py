import traceback

RADARR_URL = None
RADARR_API = None


def setURL(url):
    global RADARR_URL
    if not url.startswith("http"):
        url = "http://" + url
    if not url.endswith("/"):
        url += "/"
    RADARR_URL = url


def setAPI(api):
    global RADARR_API
    RADARR_API = api


def getMovies():
    try:
        return JSON.ObjectFromURL(RADARR_URL + "api/movie", headers={'X-Api-Key': RADARR_API})
    except Exception as e:
        Log.Debug("Error in getProfiles: " + e.message)
        Log.Error(str(traceback.format_exc()))

def getMovieById(movie_id, imdb=False):
    movies = getMovies()
    if movies:
        for movie in movies:
            if imdb:
                if str(imdb) == movie.get('imdbId'):
                    return movie.get('id')
            else:
                if int(movie_id) == movie.get('tmdbId', -1):
                    return movie.get('id')
    return -1

def getProfiles():
    try:
        return JSON.ObjectFromURL(RADARR_URL + "api/Profile", headers={'X-Api-Key': RADARR_API})
    except Exception as e:
        Log.Debug("Error in getProfiles: " + e.message)
        Log.Error(str(traceback.format_exc()))


def getProfileIDfomName(name):
    profiles = getProfiles()
    for profile in profiles:
        if profile['name'] == name:
            return profile.get('id', -1)
    return -1                               #-1 for not found

def getRootFolderPath():
    root = JSON.ObjectFromURL(RADARR_URL + "api/Rootfolder", headers={'X-Api-Key': RADARR_API})
    if root:
        return root[0]['path']
    return None


#add movie to Radarr, returns Radarr response
def addMovie(tmdb, title, year, profileId, titleSlug, monitored, rootPath, searchNow=False):
    options = {'tmdbId': tmdb, 'title': title, 'profileId': profileId, 'titleSlug': titleSlug,
               'rootFolderPath': rootPath, 'monitored': monitored, 'year': year,
               'addOptions': {'searchForMovie': searchNow}}
    values = JSON.StringFromObject(options)
    try:
        resp = HTTP.Request(RADARR_URL + "api/movie", data=values, headers={'X-Api-Key': RADARR_API})
        return resp
    except Exception as e:
        Log.Error(str(traceback.format_exc()))  # raise e
        Log.Debug("Options: " + str(options))
        Log.Debug("Error in addMovie: " + e.message)
        Log.Debug("Response Status: " + str(Response.Status))
    return None


def lookupMovie(term):
    try:
        resp = HTTP.Request(RADARR_URL + "api/movies/Lookup?term=" + String.Quote(term, True), headers={'X-Api-Key': RADARR_API})
        return resp
    except Exception as e:
        Log.Error(str(traceback.format_exc()))  # raise e
        Log.Debug("Options: " + str(options))
        Log.Debug("Error in addMovie: " + e.message)
        Log.Debug("Response Status: " + str(Response.Status))
    return []


def lookupMovieId(id, imdb=False):
    if imdb:
        url = RADARR_URL + "api/movies/Lookup/imdb?imdbId=" + str(id)
    else:
        url = RADARR_URL + "api/movies/Lookup/tmdb?tmdbId=" + str(id)
    try:
        resp = HTTP.Request(url=url, headers={'X-Api-Key': RADARR_API})
        return resp
    except Exception as e:
        Log.Error(str(traceback.format_exc()))  # raise e
        Log.Debug("Options: " + str(options))
        Log.Debug("Error in addMovie: " + e.message)
        Log.Debug("Response Status: " + str(Response.Status))
    return None



