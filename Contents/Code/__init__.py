TITLE = 'Request Channel'
PREFIX = '/video/requestchannel'

ART = 'art-default.jpg'
ICON = 'plexrequestchannel.png'

from Session import VERSION, checkCompletedMovies
from api import Plex, Email

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
########################################################

TV_SHOW_OBJECT_FIX_CLIENTS = ["Android", "Plex for Android"]

from LocalePatch import SetAvailableLanguages

LANGUAGES = ['en', 'fr', 'nl', 'de', 'it']

runs = 0
lastrun = Datetime.Now()


########################################################
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

    Plugin.AddViewGroup("Details", viewMode="InfoList", mediaType="items")
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

    Log.Debug("Channel Version: " + VERSION)

    SetAvailableLanguages(LANGUAGES)

    ## Initialize Dictionary
    if 'tv' not in Dict:
        Dict['tv'] = {}
    if 'movie' not in Dict:
        Dict['movie'] = {}
    if 'music' not in Dict:
        Dict['music'] = {}
    if 'register' not in Dict:
        Dict['register'] = {}
        Dict['register_reset'] = Datetime.TimestampFromDatetime(Datetime.Now())
    if 'blocked' not in Dict:
        Dict['blocked'] = []
    if 'sonarr_users' not in Dict:
        Dict['sonarr_users'] = []
    if 'sickbeard_users' not in Dict:
        Dict['sickbeard_users'] = []
    if 'debug' not in Dict:
        Dict['debug'] = False
    if 'DumbKeyboard-History' not in Dict:
        Dict['DumbKeyboard-History'] = []
    if 'sortbyname' not in Dict:
        Dict['sortbyname'] = True
    Dict.Save()
    Log.Debug(Network.Address)
    PeriodicScan()


def ValidatePrefs():
    return


from Session import Session

sessions = {}


###################################################################################################
# This tells Plex how to list you in the available channels and what type of channels this is
@handler(PREFIX, TITLE, art=ART, thumb=ICON)
@route(PREFIX + '/main')
def MainMenu():
    client_id = Request.Headers.get("X-Plex-Client-Identifier")
    if client_id:
        session_id = Hash.MD5(client_id)
    else:
        session_id = Hash.MD5(str(Datetime.Now()))
    if session_id in sessions:  # Prior session started, continue
        sesh = sessions[session_id]
    else:  # Create a new session
        sesh = Session(session_id=session_id)
        sessions[session_id] = sesh
    return sesh.SMainMenu()


def PeriodicScan():
    checkCompletedMovies()
    Thread.CreateTimer(60, PeriodicScan)


"""
List of Client.Product and Client.Platform

Client.Product 	        Description
--------------          ------------------------------------------------------------------
Plex for Android 	    Android phone
Plex for iOS 	        Apple phone
Plex Home Theater 	    This is for Plex Home Theater
Plex Media Player 	    This is for new Plex Media Player
Plex Web 	            Plex Web client, from web browser
Plex for Firefox TV 	Plex Firefox TV, (source), this one is a guess
Plex for Roku 	        Roku
OpenPHT 	            OpenPHT
Plex Chromecast 	    Chromecast
NotifyPlex 	            NZBGet
HTPC Manager 	        Windows Server (Windows-2012Server-6.2.9200). Not sure if correct.
Plex for Xbox One 	    Xbox One
Plex for Xbox 360       Xbox 360
Plex for Samsung        Samsung

Client.Platform 	    Description
---------------         -------------------------------------------------------------------
Android 	            Android phone
iOS 	                Apple phone
Safari 	                This is a guess from looking at a Service URL code.
Chrome              	Plex Web client on Chrome internet browser
Plex Home Theater 	    This is for Plex Home Theater
Konvergo 	            Plex Media Player, (running on a Raspberry PI 2 B)
tvOS 	                New AppleTV
MacOSX 	                MacOSX
Linux 	                Linux
Windows 	            Windows
LGTV 	                LGTV
Roku 	                Roku
Chromecast          	Chromecast
NZBGet 	                NZBGet
Xbox One            	Xbox One
Xbox 360                Xbox 360
Samsung                 Samsung


Screenshots: http://imgur.com/a/cxKU9/all
"""
