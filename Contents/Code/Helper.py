from api import *

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
########################################################

### Notification Constants #############################
PUSHBULLET_API_URL = "https://api.pushbullet.com/v2/"
PUSHOVER_API_URL = "https://api.pushover.net/1/messages.json"
PUSHOVER_API_KEY = "ajMtuYCg8KmRQCNZK2ggqaqiBw2UHi"
PUSHALOT_API_URL = "https://pushalot.com/api/sendmessage"
SLACK_API_URL = "https://slack.com/api/"
########################################################

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

def setupApi():
    Plex.setIp("127.0.0.1")
    Plex.setPort("32400")
    Radarr.setAPI(Prefs['radarr_api'])
    Radarr.setURL(Prefs['radarr_url'])
    Couchpotato.setAPI(Prefs['couchpotato_api'])
    Couchpotato.setURL(Prefs['couchpotato_url'])
    if Prefs['pushbullet_api']:
        Pushbullet.setAPI(Prefs['pushbullet_api'])
    if Prefs['pushalot_api']:
        Pushalot.setAPI(Prefs['pushalot_api'])
    if Prefs['pushover_api']:
        Pushover.setAPI(Prefs['pushover_api'])
    if Prefs['slack_api']:
        Slack.setAPI(Prefs['slack_api'])
        Slack.setUser(Prefs['slack_user'])



