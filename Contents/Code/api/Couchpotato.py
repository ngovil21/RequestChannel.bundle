import traceback

COUCHPOTATO_API = None
COUCHPOTATO_URL = None

def setAPI(api):
    global COUCHPOTATO_API
    COUCHPOTATO_API = api

def setURL(url):
    global COUCHPOTATO_URL
    if not url.startswith("http"):
        url = "http://" + url
    if not url.endswith("/"):
        url += "/"
    COUCHPOTATO_URL = url

def getProfiles():
    try:
        profiles = JSON.ObjectFromURL(COUCHPOTATO_URL + "api/" + COUCHPOTATO_API + "/profile.list/")
        if 'success' in profiles:
            return profiles
    except Exception as e:
        Log.Debug("Error in getProfiles: " + e.message)
        Log.Error(str(traceback.format_exc()))  # raise last error
    return None

#return id for name else -1
def getProfileIdFromName(name):
    profiles = getProfiles()
    if not profiles:
        return -1
    for key in profiles['list']:
        if key['label'] == name:
            return key['_id']
    return -1

def getCategories():
    try:
        cat = JSON.ObjectFromURL(COUCHPOTATO_URL + "api/" + COUCHPOTATO_API + "/profile.list/")
        if 'success' in cat:
            return cat
    except Exception as e:
        Log.Debug("Error in getProfiles: " + e.message)
        Log.Error(str(traceback.format_exc()))  # raise last error
    return None

def getCategoryIdFromName(name):
    cat = getProfiles()
    if not cat:
        return -1
    for key in cat['list']:
        if key['label'] == name:
            return key['_id']
    return -1

#add movie to Couchpotato with imdb, profile id, category id, return result page
def addMovie(imdb, profile=-1, category=-1):
    values = {'identifier': imdb}
    if profile > -1:
        values['profile_id'] = profile
    if category > -1:
        values['category_id'] = category
    try:
        json = JSON.ObjectFromURL(COUCHPOTATO_URL + "api/" + COUCHPOTATO_API + "/movie.add/", values=values)
        if 'success' in json and json['success']:
            return json
    except Exception as e:
        Log.Debug("Error in addMovie: " + e.message)
        Log.Error(str(traceback.format_exc()))  # raise last error
    return None


def getMovieList(status=None):
    if status:
        values = {'status': status}
    try:
        movie_list = JSON.ObjectFromURL(COUCHPOTATO_URL + "api/" + COUCHPOTATO_API + "/movie.list/", values)
        if movie_list['success'] and not movie_list['empty']:
            return movie_list['movies']
        elif movie_list['empty']:
            return {}
    except Exception as e:
        Log.Debug("Error in getMovieList: " + e.message)
        Log.Error(str(traceback.format_exc()))  # raise last error
    return None

def deleteMovie(movie_id, delete_from="wanted"):
    try:
        movie_delete = JSON.ObjectFromURL(COUCHPOTATO_URL + "api/" + COUCHPOTATO_API + "/movie.delete",
                                          values=dict(id=movie_id, delete_from=delete_from))
        if movie_delete['success']:
            return True
    except Exception as e:
        Log.Debug("Error in deleteMovie: " + e.message)
        Log.error(str(traceback.format_exc()))  # raise e
    return False



