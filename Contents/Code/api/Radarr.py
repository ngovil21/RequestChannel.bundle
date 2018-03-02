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

def check():
    try:
        available = JSON.ObjectFromURL(RADARR_URL + "api/system/status", headers={'X-Api-Key': RADARR_API})
        return "version" in available
    except Exception as e:
        Log.Debug("Error in checkConnection: " + e.message)
        Log.Error(str(traceback.format_exc()))  # raise last error
    return False

def getMovies():
    try:
        return JSON.ObjectFromURL(RADARR_URL + "api/movie", headers={'X-Api-Key': RADARR_API})
    except Exception as e:
        Log.Debug("Error in getMovies: " + e.message)
        Log.Error(str(traceback.format_exc()))

def getMovieById(movie_id, imdb=False):
    movies = getMovies()
    if movies:
        for movie in movies:
            if imdb:
                if str(movie_id) == movie.get('imdbId'):
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
def addMovie(tmdb, title, year, profileId, titleSlug, monitored, rootPath, searchNow=False, cleanTitle=None, images=None):
    options = {'tmdbId': tmdb, 'title': title, 'profileId': profileId, 'titleSlug': titleSlug,
               'rootFolderPath': rootPath, 'monitored': monitored, 'year': year, 'cleanTitle': cleanTitle,
               'images': images, 'addOptions': {'searchForMovie': searchNow}}
    values = JSON.StringFromObject(options)
    try:
        #resp = JSON.ObjectFromURL(RADARR_URL + "api/movie", values=options, headers={'X-Api-Key': RADARR_API})
        resp = HTTP.Request(RADARR_URL + "api/movie", data=values, headers={'X-Api-Key': RADARR_API}, immediate=True)
        Log.Debug(str(resp.content))
        return True
        #return JSON.ObjectFromString(resp.content)
    except Exception as e:
        Log.Error(str(traceback.format_exc()))  # raise e
        Log.Debug("Options: " + str(options))
        Log.Debug("Error in addMovie: " + e.message)
        Log.Debug("Response Status: " + str(Response.Status))
    return None


def lookupMovie(term):
    try:
        resp = JSON.ObjectFromURL(RADARR_URL + "api/movies/Lookup?term=" + String.Quote(term, True), headers={'X-Api-Key': RADARR_API})
        return resp
    except Exception as e:
        Log.Error(str(traceback.format_exc()))  # raise e
        Log.Debug("Term: " + term)
        Log.Debug("Error in lookupMovie: " + e.message)
        Log.Debug("Response Status: " + str(Response.Status))
    return []


def lookupMovieId(id, imdb=False):
    if imdb:
        url = RADARR_URL + "api/movies/Lookup/imdb?imdbId=" + str(id)
    else:
        url = RADARR_URL + "api/movies/Lookup/tmdb?tmdbId=" + str(id)
    try:
        return JSON.ObjectFromURL(url=url, headers={'X-Api-Key': RADARR_API})
    except Exception as e:
        Log.Error(str(traceback.format_exc()))  # raise e
        Log.Debug("Movie ID:" + str(id))
        Log.Debug("Error in lookupMovieId: " + e.message)
        Log.Debug("Response Status: " + str(Response.Status))
    return None



