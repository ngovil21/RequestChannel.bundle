import traceback

TMDB_API_URL = "http://api.themoviedb.org/3/"
TMDB_IMAGE_BASE_URL = "http://image.tmdb.org/t/p/"
POSTER_SIZE = "w500/"
BACKDROP_SIZE = "original/"

TMDB_API_KEY = None

LANGUAGE_ABBREVIATIONS = {
    "English": "en",
    "Espanol": "es",
    "Francais": "fr",
    "Deutsch": "de",
    "Italiano": "it",
    "Chinese": "zh",
    "Nederlands": "nl",
    "Svenska": "sv",
    "Norsk": "no",
    "Dansk": "da",
    "Suomeksi": "fi",
    "Polski": "pl",
    "Magyar": "hu",
    "Greek": "el",
    "Turkish": "tr",
    "Russian": "ru",
    "Hebrew": "he",
    "Japanese": "ja",
    "Portuguese": "pt",
    "Czech": "cs",
    "Slovenian": "sl",
    "Croatian": "hr",
    "Korean": "ko"
}


def setAPI(key):
    global TMDB_API_KEY
    TMDB_API_KEY = key


# Searches TMDB and returns a json list of results
def Search(query, language="English"):
    try:
        url = TMDB_API_URL + "search/movie?api_key=" + TMDB_API_KEY + "&language=" + LANGUAGE_ABBREVIATIONS.get(
            language, "en") + "&query=" + query
        request = JSON.ObjectFromURL(url, headers={'Accept': 'application/json'})
        if 'results' in request:
            return request
    except Exception as e:
        Log.Debug("Error in Search: " + e.message)
        Log.Error(str(traceback.format_exc()))  # raise last error
    return {}

#parse a tmdb result to return a dict with title, year, poster, plot
def parseResult(result):
    info = {'id': result.get('id')}
    info['title'] = result.get('title')
    if result['release_data']:
        info['year'] = result['release_date'][0:4]
        date = result['release_date']
        rel_date = Datetime.ParseDate(date)
        if rel_date:
            info['date'] = rel_date.date()
    else:
        info['year'] = None
        info['date'] = None
    if result['poster_path']:
        info['thumb'] = TMDB_IMAGE_BASE_URL + POSTER_SIZE + result['poster_path']
    if result['backdrop_path']:
        info['art'] = TMDB_IMAGE_BASE_URL + BACKDROP_SIZE + result['backdrop_path']
    if result['overview']:
        info['summary'] = result['overview']
    return info

# Query TMDB for a movie with IMDB id
def findMovieByIMDB(imdb, language="English"):
    try:
        json = JSON.ObjectFromURL(
            TMDB_API_URL + "find/" + imdb + "?api_key=" + TMDB_API_KEY + "&language=" + LANGUAGE_ABBREVIATIONS.get(
                language, "en") + "&external_source=imdb_id",
            headers={'Accept': 'application/json'})
        if json.get('movie_results'):  # imdb id should be specific, return first result
            return json['movie_results'][0]['id']
        else:
            Log.Debug("IMDB " + imdb + " not found in TMDB!")
    except Exception as e:
        Log.Debug("Error in getMovieByIMDB: " + e.message)
        Log.Error(str(traceback.format_exc()))  # raise last error
    return None


# returns IMDB id from tmdb id
def getIMDB(tmdb):
    try:
        json = JSON.ObjectFromURL(TMDB_API_URL + "movie/" + tmdb + "?api_key=" + TMDB_API_KEY,
                                  headers={'Accept': 'application/json'})
        return json.get('imdb_id', None)
    except Exception as e:
        Log.Debug("Error in getIMDB: " + e.message)
        Log.Error(str(traceback.format_exc()))  # raise last error
    return None


