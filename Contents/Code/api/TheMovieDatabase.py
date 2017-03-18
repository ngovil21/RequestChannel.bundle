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
    url = TMDB_API_URL + "search/movie?api_key=" + TMDB_API_KEY + "&language=" + LANGUAGE_ABBREVIATIONS.get(
        language, "en") + "&query=" + query
    request = JSON.ObjectFromURL(url, headers={'Accept': 'application/json'})

    if 'results' in request:
        return request
    else:
        return {}


#Query TMDB for a movie with IMDB id
def getMovieByIMDB(imdb, language="English"):
    json = JSON.ObjectFromURL(
        TMDB_API_URL + "find/" + imdb + "?api_key=" + TMDB_API_KEY + "&language=" + LANGUAGE_ABBREVIATIONS.get(
            language, "en") + "&external_source=imdb_id",
        headers={'Accept': 'application/json'})
    if json.get('movie_results'):                       #imdb id should be specific, return first result
        return json['movie_results'][0]['id']
    Log.Debug("IMDB " + imdb + " not found in TMDB!")
    return None


def getIMDB(tmdb):
    json = JSON.ObjectFromURL(TMDB_API_URL + "movie/" + tmdb + "?api_key=" + TMDB_API_KEY,
                              headers={'Accept': 'application/json'})
    return json.get('imdb_id')
