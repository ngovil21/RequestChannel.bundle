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
    for key in cat['list']:
        if key['label'] == name:
            return key['_id']
    return -1

#add movie to Couchpotato with imdb, profile id, category id, return result page
def addMovie(imdb, profile=None, category=None):
    values = {'identifier': imdb}
    if profile:
        values['profile_id'] = profile
    if category:
        values['category_id'] = category
    try:
        json = JSON.ObjectFromURL(COUCHPOTATO_URL + "api/" + COUCHPOTATO_API + "/movie.add/", values=values)
        if 'success' in json and json['success']:
            return json
    except Exception as e:
        Log.Debug("Error in addMovie: " + e.message)
        Log.Error(str(traceback.format_exc()))  # raise last error
    return None



