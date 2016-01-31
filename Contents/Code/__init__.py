TITLE = 'Plex Request Channel'
PREFIX = '/video/plexrequestchannel'

ART = 'art-default.jpg'
ICON = 'plexrequestchannel.png'

DATA_FILE = "Requests"

MOVIE_DB = "OpenMovieDatabase"

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
#######################################################

### Notification Constants ############################
PUSHBULLET_API_URL = "https://api.pushbullet.com/v2/"
PUSHOVER_API_URL = "https://api.pushover.net/1/messages.json"
PUSHOVER_API_KEY = "ajMtuYCg8KmRQCNZK2ggqaqiBw2UHi"

#######################################################
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
    Plugin.AddViewGroup("Grid", viewMode="Posters", mediaType="items")

    if not 'tv' in Dict or not 'movie' in Dict:
        Dict.Reset()
        Dict['tv'] = {}
        Dict['movie'] = {}
        Dict.Save()


###################################################################################################
# This tells Plex how to list you in the available channels and what type of channels this is
@handler(PREFIX, TITLE, art=ART, thumb=ICON)
@route(PREFIX + '/mainmenu')
def MainMenu(locked='locked', message=None):
    Log.Debug("Client: " + str(Client.Platform))
    oc = ObjectContainer(replace_parent=True, message=message)

    oc.add(DirectoryObject(key=Callback(AddNewMovie, title="Request a Movie", locked=locked), title="Request a Movie"))
    oc.add(DirectoryObject(key=Callback(AddNewTVShow, title="Request a TV Show", locked=locked), title="Request a TV Show"))
    if locked=='unlocked' or Prefs['password'] is None or Prefs['password'] == "":
        oc.add(DirectoryObject(key=Callback(ViewRequests, locked='unlocked'), title="View Requests"))                #No password needed this session
    else:
        oc.add(DirectoryObject(key=Callback(ViewRequestsPassword, locked='locked'), title="View Requests"))         #Set View Requests to locked and ask for password

    return oc


@route(PREFIX + '/addnewmovie')
def AddNewMovie(title, locked='unlocked'):
    oc = ObjectContainer(header=TITLE, message="Please enter the movie name in the searchbox and press enter.")
    oc.add(InputDirectoryObject(key=Callback(SearchMovie, title="Search Results", locked=locked), title=title, prompt="Enter the name of the movie:"))
    return oc


@route(PREFIX + '/searchmovie')
def SearchMovie(title, query, locked='unlocked'):
    oc = ObjectContainer(title1=title,content=ContainerContent.Movies, view_group="Grid")
    query = String.Quote(query, usePlus=True)
    if Prefs['movie_db'] == "TheMovieDatabase":
        headers = {
            'Accept': 'application/json'
        }
        request = JSON.ObjectFromURL(url=TMDB_API_URL + "search/movie?api_key=" + TMDB_API_KEY + "&query=" + query, headers=headers)
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
                oc.add(DirectoryObject(key=Callback(ConfirmMovieRequest, id=key['id'], title=key['title'], year=year, poster=thumb, backdrop=art,
                                                    summary=key['overview'], locked=locked), title=title_year, thumb=thumb, summary=key['overview'], art=art))
            else:
                Log.Debug("No Results Found")
                oc.add(InputDirectoryObject(key=Callback(SearchMovie, title="Search Results", locked=locked), title="Search Again",
                                            prompt="Enter the name of the movie:"))
                oc = ObjectContainer(header=TITLE, message="Sorry there were no results found for your search.")
                oc.add(DirectoryObject(key=Callback(MainMenu, locked=locked), title="Back to Main Menu", thumb=R('return.png')))
                return oc
    else:  # Use OMDB By Default
        request = JSON.ObjectFromURL(url=OMDB_API_URL + "?s=" + query + "&r=json")
        if 'Search' in request:
            results = request['Search']
            for key in results:
                if not key['Title']:
                    continue
                if 'type' in key and not (key['type'] == "movie"):  # only show movie results
                    continue
                title_year = key['Title'] + " (" + key['Year'] + ")"
                oc.add(
                    DirectoryObject(key=Callback(ConfirmMovieRequest, id=key['imdbID'], title=key['Title'], year=key['Year'], poster=key['Poster'], locked=locked),
                                    title=title_year, thumb=key['Poster']))
        else:
            Log.Debug("No Results Found")
            oc = ObjectContainer(header=TITLE, message="Sorry there were no results found for your search.")
            oc.add(InputDirectoryObject(key=Callback(SearchMovie, title="Search Results", locked=locked), title="Search Again",
                                        prompt="Enter the name of the movie:"))
            oc.add(DirectoryObject(key=Callback(MainMenu, locked=locked), title="Back to Main Menu", thumb=R('return.png')))
            return oc
    return oc


@route(PREFIX + '/confirmmovierequest')
def ConfirmMovieRequest(id, title, year="", poster="", backdrop="", summary="", locked='unlocked'):
    title_year = title + " " + "(" + year + ")"
    oc = ObjectContainer(title1="Confirm Movie Request", title2="Are you sure you would like to request the movie " + title_year + "?")

    oc.add(
        DirectoryObject(key=Callback(AddMovieRequest, id=id, title=title, year=year, poster=poster, backdrop=backdrop, summary=summary, locked=locked), title="Yes", thumb=R('check.png')))
    oc.add(DirectoryObject(key=Callback(MainMenu, locked=locked), title="No", thumb=R('x-mark.png')))

    return oc

@indirect
@route(PREFIX + '/addmovierequest')
def AddMovieRequest(id, title, year="", poster="", backdrop="", summary="", locked='unlocked'):
    if id in Dict['movie']:
        Log.Debug("Movie is already requested")
        oc = ObjectContainer(header=TITLE, message="Movie has already been requested.")
        oc.add(DirectoryObject(key=Callback(MainMenu, locked=locked), title="Return to Main Menu", thumb=R('return.png')))
        return MainMenu(locked=locked, message="Movie has already been requested")
    else:
        title_year = title + " (" + year + ")"
        Dict['movie'][id] = {'type': 'movie', 'id': id, 'title': title, 'year': year, 'title_year':title_year, 'poster': poster, 'backdrop': backdrop, 'summary': summary}
        Dict.Save()
        if Prefs['couchpotato_autorequest']:
            SendToCouchpotato(id)
        Notify(id=id, type='movie')
        oc = ObjectContainer(header=TITLE, message="Movie has been requested.")
        oc.add(DirectoryObject(key=Callback(MainMenu, locked=locked), title="Return to Main Menu", thumb=R('return.png')))
        return MainMenu(locked=locked, message="Movie has been requested")


@route(PREFIX + '/addtvshow')
def AddNewTVShow(title="", locked='unlocked'):
    oc = ObjectContainer(header=TITLE, message="Please enter the movie name in the searchbox and press enter.")
    oc.add(InputDirectoryObject(key=Callback(SearchTV, locked=locked), title="Request a TV Show", prompt="Enter the name of the TV Show:"))
    return oc


@route(PREFIX + '/searchtv')
def SearchTV(query, locked='unlocked'):
    oc = ObjectContainer(title1="Search Results", content=ContainerContent.Shows, view_group="Grid")
    query = String.Quote(query, usePlus=True)
    xml = XML.ElementFromURL(TVDB_API_URL + "GetSeries.php?seriesname=" + query)
    series = xml.xpath("//Series/seriesid")
    if len(series) == 0:
        oc = ObjectContainer(header=TITLE, message="Sorry there were no results found.")
        oc.add(InputDirectoryObject(key=Callback(SearchTV, locked=locked), title="Search Again", prompt="Enter the name of the TV Show:"))
        oc.add(DirectoryObject(key=Callback(MainMenu, locked=locked), title="Return to Main Menu", thumb=R('return.png')))
        return oc
    count = 0
    for serie in series:
        id = ""
        title = ""
        year = ""
        poster = ""
        summary = ""
        for child in serie.getchildren():
            if child.tag.lower() == "seriesid" and child.text:
                id = child.text
            elif child.tag.lower() == "seriesname" and child.text:
                title = child.text
            elif child.tag.lower() == "banner" and child.text and not poster:
                poster = TVDB_BANNER_URL + child.text
            elif child.tag.lower() == "overview" and child.text:
                summary = child.text
            elif child.tag.lower() == "firstaired" and child.text:
                release_date = child.text
                year = release_date[0:4]
            elif child.tag.lower() == "poster" and child.text:
                poster = TVDB_BANNER_URL + child.text
        if not serie.text:
            continue
        id = serie.text
        if count < 6:                   #Let's look for the actual poster for the first 5 tv shows to reduce api hits
            try:
                serie_page = XML.ElementFromURL(TVDB_API_URL + TVDB_API_KEY + "/series/" + id)
                poster_text = serie_page.xpath("//Series/poster/text")[0]
                if poster_text:
                    Log.Debug(poster_text)
                    poster = TVDB_BANNER_URL + poster_text
            except:
                pass
            count+=1
        if id == "":
            Log.Debug("No id found!")
        if year:
            title_year = title + " (" + year + ")"
        else:
            title_year = title

        oc.add(DirectoryObject(key=Callback(ConfirmTVRequest, id=id, title=title, year=year, poster=poster, summary=summary, locked=locked), title=title_year,
                               thumb=poster))

    return oc


@route(PREFIX + '/confirmtvrequest')
def ConfirmTVRequest(id, title, year="", poster="", backdrop="", summary="", locked='unlocked'):
    if year:
        title_year = title + " " + "(" + year + ")"
    else:
        title_year = title
    oc = ObjectContainer(title1="Confirm TV Request", title2="Are you sure you would like to request the TV Show " + title_year + "?")

    oc.add(DirectoryObject(key=Callback(AddTVRequest, id=id, title=title, year=year, poster=poster, backdrop=backdrop, summary=summary, locked=locked), title="Yes", thumb=R('check.png')))
    oc.add(DirectoryObject(key=Callback(MainMenu, locked=locked), title="No", thumb=R('x-mark.png')))

    return oc

@indirect
@route(PREFIX + '/addtvrequest')
def AddTVRequest(id, title, year="", poster="", backdrop="", summary="", locked='unlocked'):
    if id in Dict['tv']:
        Log.Debug("TV Show is already requested")
        return MainMenu(locked=locked, message="TV Show has already been requested")
    else:
        Dict['tv'][id] = {'type': 'tv', 'id': id, 'title': title, 'year': year, 'poster': poster, 'backdrop': backdrop, 'summary': summary}
        Dict.Save()
        if Prefs['sonarr_autorequest']:
            SendToSonarr(id)
        Notify(id=id, type='tv')
        oc = ObjectContainer(header=TITLE, message="TV Show has been requested.")
        oc.add(DirectoryObject(key=Callback(MainMenu, locked=locked), title="Return to Main Menu", thumb=R('return.png')))

        return MainMenu(locked=locked, message="TV Show has been requested")


@route(PREFIX + '/viewrequests')
def ViewRequests(query="", locked='unlocked', message=None):
    if locked == 'unlocked':
        oc = ObjectContainer(content=ContainerContent.Mixed, message=message)
    elif query == Prefs['password']:
        locked = 'unlocked'
        oc = ObjectContainer(header=TITLE, message="Password is correct", content=ContainerContent.Mixed)
    else:
        oc = ObjectContainer(header=TITLE, message="Password is incorrect!")
        oc.add(DirectoryObject(key=Callback(MainMenu, locked=locked), title="Return to Main Menu"))
        return oc
    if not Dict['movie'] and not Dict['tv']:
        Log.Debug("There are no requests")
        oc = ObjectContainer(header=TITLE, message="There are currently no requests.")
        oc.add(DirectoryObject(key=Callback(MainMenu, locked='unlocked'), title="Return to Main Menu", thumb=R('return.png')))
        return oc
    else:
        for id in Dict['movie']:
            d = Dict['movie'][id]
            title_year = d['title'] + " (" + d['year'] + ")"
            oc.add(DirectoryObject(key=Callback(ViewRequest, id=id, type=d['type'], locked=locked), title=title_year, thumb=d['poster'], summary=d['summary'],
                                   art=d['backdrop']))
        if Dict['tv']:
            for id in Dict['tv']:
                d = Dict['tv'][id]
                title_year = d['title'] + " (" + d['year'] + ")"
                oc.add(DirectoryObject(key=Callback(ViewRequest, id=id, type=d['type'], locked=locked), title=title_year, thumb=d['poster'], summary=d['summary'],
                                       art=d['backdrop']))
    oc.add(DirectoryObject(key=Callback(MainMenu, locked=locked), title="Return to Main Menu", thumb=R('return.png')))
    if len(oc) > 1:
        oc.add(DirectoryObject(key=Callback(ConfirmDeleteRequests, locked=locked), title="Clear All Requests", thumb=R('trash.png')))
    return oc


@route(PREFIX + '/getrequestspassword')
def ViewRequestsPassword(locked='locked'):
    oc = ObjectContainer(header=TITLE, message="Please enter the password in the searchbox")
    oc.add(InputDirectoryObject(key=Callback(ViewRequests, locked=locked), title="Enter password:", prompt="Please enter the password:"))
    return oc

@route(PREFIX + '/confirmclearrequests')
def ConfirmDeleteRequests(locked='unlocked'):
    oc = ObjectContainer(title2="Are you sure you would like to clear all requests?")
    oc.add(DirectoryObject(key=Callback(ClearRequests, locked=locked), title="Yes", thumb=R('check.png')))
    oc.add(DirectoryObject(key=Callback(ViewRequests,  locked=locked), title="No", thumb=R('x-mark.png')))
    return oc

@indirect
@route(PREFIX + '/clearrequests')
def ClearRequests(locked='unlocked'):
    Dict['tv'] = {}
    Dict['movie'] = {}
    Dict.Save()
    return ViewRequests(locked=locked, message="All requests have been cleared")

@route(PREFIX + '/viewrequest')
def ViewRequest(id, type, locked='unlocked'):
    key = Dict[type][id]
    title_year = key['title'] + " (" + key['year'] + ")"
    oc = ObjectContainer(title2=title_year)
    oc.add(DirectoryObject(key=Callback(ConfirmDeleteRequest, id=id, type=type, title_year=title_year, locked=locked), title="Delete Request", thumb=R('x-mark.png')))
    if key['type'] == 'movie':
        if Prefs['couchpotato_url'] and Prefs['couchpotato_api']:
            oc.add(DirectoryObject(key=Callback(SendToCouchpotato, id=id, locked=locked), title="Send to CouchPotato", thumb=R('couchpotato.png')))
    if key['type'] == 'tv':
        if Prefs['sonarr_url'] and Prefs['sonarr_api']:
            oc.add(DirectoryObject(key=Callback(SendToSonarr, id=id, locked=locked), title="Send to Sonarr", thumb=R('sonarr.png')))
    oc.add(DirectoryObject(key=Callback(ViewRequests, locked=locked), title="Return to View Requests", thumb=R('return.png')))
    return oc


@route(PREFIX + '/confirmdeleterequest')
def ConfirmDeleteRequest(id, type, title_year="", locked='unlocked'):
    oc = ObjectContainer(title2="Are you sure you would like to delete the request for " + title_year + "?")
    oc.add(DirectoryObject(key=Callback(DeleteRequest, id=id, type=type, locked=locked), title="Yes", thumb=R('check.png')))
    oc.add(DirectoryObject(key=Callback(ViewRequest, id=id, type=type, locked=locked), title="No", thumb=R('x-mark.png')))
    return oc

@indirect
@route(PREFIX + '/deleterequest')
def DeleteRequest(id, type, locked='unlocked'):
    if id in Dict[type]:
        # oc = ObjectContainer(header=TITLE, message="Request was deleted!")
        message = "Request was deleted"
        del Dict[type][id]
        Dict.Save()
    else:
        # oc = ObjectContainer(header=TITLE, message="Request could not be deleted!")
        message = "Request could not be deleted"
    # oc.add(DirectoryObject(key=Callback(ViewRequests, locked=locked), title="Return to View Requests", thumb=R('return.png')))
    return ViewRequests(locked=locked, message=message)


@route(PREFIX + '/sendtocouchpotato')
def SendToCouchpotato(id, locked='unlocked'):
    if not id.startswith("tt"):  # Check if id is an imdb id
        # we need to convert tmdb id to imdb
        json = JSON.ObjectFromURL(TMDB_API_URL + "movie/id/?api_key=" + TMDB_API_KEY, headers={'Accept': 'application/json'})
        if 'imdb_id' in json and json['imdb_id']:
            imdb_id = json['imdb_id']
        else:
            oc = ObjectContainer(header=TITLE, message="Unable to get IMDB id for movie, add failed...")
            oc.add(DirectoryObject(key=Callback(ViewRequests, locked=locked), title="Return to View Requests"))
            return oc
    else:
        imdb_id = id
    # we have an imdb id, add to couchpotato
    if not Prefs['couchpotato_url'].startswith("http"):
        couchpotato_url = "http://" + Prefs['couchpotato_url']
    else:
        couchpotato_url = Prefs['couchpotato_url']
    if not couchpotato_url.endswith("/"):
        couchpotato_url = couchpotato_url + "/"
    values={}
    values['identifier'] = imdb_id
    if Prefs['couchpotato_profile']:
        cat = JSON.ObjectFromURL(couchpotato_url + "api/" + Prefs['couchpotato_api'] + "/profile.list/")
        if cat['success']:
            for key in cat['list']:
                if key['label'] == Prefs['couchpotato_profile']:
                    values['profile_id'] = key['_id']
        else:
            Log.Debug("Unable to open up Couchpotato Profile List")
    if Prefs['couchpotato_category']:
        cat = JSON.ObjectFromURL(couchpotato_url + "api/" + Prefs['couchpotato_api'] + "/category.list/")
        if cat['success']:
            for key in cat['categories']:
                if key['label'] == Prefs['couchpotato_category']:
                    values['category_id'] = key['_id']
        else:
            Log.Debug("Unable to open up Couchpotato Category List")
    json = JSON.ObjectFromURL(couchpotato_url + "api/" + Prefs['couchpotato_api'] + "/movie.add/", values=values)
    if 'success' in json and json['success']:
        oc = ObjectContainer(header=TITLE, message="Movie Request Sent to CouchPotato!")
    else:
        oc = ObjectContainer(header=TITLE, message="Movie Request failed!")
    key = Dict['movie'][id]
    title_year = key['title'] + " (" + key['year'] + ")"
    oc.add(DirectoryObject(key=Callback(ConfirmDeleteRequest, id=id, type='movie', title_year=title_year, locked=locked), title="Delete Request"))
    oc.add(DirectoryObject(key=Callback(ViewRequests, locked=locked), title="Return to View Requests"))
    return oc


@route(PREFIX + '/sendtosonarr')
def SendToSonarr(id, locked='unlocked'):
    oc = ObjectContainer(header=TITLE, message="Show has been sent to Sonarr.")
    if not Prefs['sonarr_url'].startswith("http"):
        sonarr_url = "http://" + Prefs['sonarr_url']
    else:
        sonarr_url = Prefs['sonarr_url']
    if not sonarr_url.endswith("/"):
        couchpotato_url = sonarr_url + "/"
    title = Dict['tv'][id]['title']
    api_header = {
        'X-Api-Key': Prefs['sonarr_api']
    }
    lookup_json = JSON.ObjectFromURL(sonarr_url + "api/Series/Lookup?term=tvdbid:" + id, headers=api_header)
    found_show = None
    for show in lookup_json:
        if show['tvdbId'] == id:
            found_show = show
    if not found_show:
        found_show = lookup_json[0]

    profile_json = JSON.ObjectFromURL(sonarr_url + "api/Profile", headers=api_header)
    profile_id = 1
    for profile in profile_json:
        if profile['name'] == Prefs['sonarr_profile']:
            profile_id = profile['id']
            break

    rootFolderPath = ""
    if Prefs['sonarr_path']:
        rootFolderPath = Prefs['sonarr_path']
    else:
        root = JSON.ObjectFromURL(sonarr_url + "api/Rootfolder", headers=api_header)
        if root:
            rootFolderPath = root[0]['path']

    Log.Debug("Profile id: " + str(profile_id))
    options = {}
    options['title'] = found_show['title']
    options['tvdbId'] = found_show['tvdbId']
    options['qualityProfileId'] = int(profile_id)
    options['titleSlug'] = found_show['titleSlug']
    options['rootFolderPath'] = rootFolderPath
    options['seasons'] = found_show['seasons']
    options['monitored'] = True

    add_options = {'ignoreEpisodesWithFiles': False,
                   'ignoreEpisodesWithoutFiles': False,
                   'searchForMissingEpisodes': True
                   }

    if Prefs['sonarr_monitor'] == 'all':
        for season in options['seasons']:
            season['monitored'] = True
    elif Prefs['sonarr_monitor'] == 'future':
        add_options['ignoreEpisodesWithFiles'] = True
        add_options['ignoreEpisodesWithoutFiles'] = True
    elif Prefs['sonarr_monitor'] == 'latest':
        options['seasons'][len(options['seasons'])-1]['monitored'] = True
    elif Prefs['sonarr_monitor'] == 'first':
        options['season'][1]['monitored'] = True
    elif Prefs['sonarr_monitor'] == 'missing':
        add_options['ignoreEpisodesWithFiles'] = True
    elif Prefs['sonarr_monitor'] == 'existing':
        add_options['ignoreEpisodesWithoutFiles'] = True
    elif Prefs['sonarr_monitor'] == 'none':
        options['monitored'] = False
    options['addOptions'] = add_options
    values = JSON.StringFromObject(options)
    try:
        HTTP.Request(sonarr_url + "api/Series",data=values, headers=api_header)
    except:
        oc = ObjectContainer(header=TITLE, message="Could not send show to Sonarr!")

    oc.add(DirectoryObject(key=Callback(ConfirmDeleteRequest, id=id, type='tv', title_year=title, locked=locked), title="Delete Request"))
    oc.add(DirectoryObject(key=Callback(ViewRequests, locked=locked), title="Return to View Requests"))
    oc.add(DirectoryObject(key=Callback(MainMenu, locked=locked), title="Return to Main Menu"))
    return oc

#Notify user of requests
def Notify(id, type):
    if Prefs['pushbullet_api']:
        # import base64
        # encode = base64.encodestring('%s:%s' % (Prefs['pushbullet_api'], "")).replace('\n', '')
        api_header = {'Authorization': 'Bearer ' + Prefs['pushbullet_api'],
                      'Content-Type': 'application/json'
                      }
        try:
            if type == 'movie':
                movie = Dict['movie'][id]
                title_year = movie['title'] + " (" + movie['year'] + ")"
                data = {'type':'note'}
                data['title'] = "Plex Request Channel - New Movie Request"
                data['body'] = "A user has requested a new movie.\n" + title_year + "\nIMDB id: " + id + "\nPoster: " + movie['poster']
                values = JSON.StringFromObject(data)
                response = HTTP.Request(PUSHBULLET_API_URL + "pushes",data=values, headers=api_header)
                if response:
                    Log.Debug("Pushbullet notification sent for :" + id)
            elif type == 'tv':
                tv = Dict['tv'][id]
                data = {'type': 'note'}
                data['title'] = "Plex Request Channel - New TV Show Request"
                data['body'] = "A user has requested a new tv show.\n" + tv['title'] + "\nTVDB id: " + id + "\nPoster: " + tv['poster']
                values = JSON.StringFromObject(data)
                response = HTTP.Request(PUSHBULLET_API_URL + "pushes", data=values, headers=api_header)
                if response:
                    Log.Debug("Pushbullet notification sent for :" + id)
        except Exception as e:
            Log.Debug("Pushbullet failed: " + e.message)
    if Prefs['pushover_user']:
        try:
            if type == 'movie':
                movie = Dict['movie'][id]
                title_year = movie['title'] + " (" + movie['year'] + ")"
                data = {'token': PUSHOVER_API_KEY}
                data['user'] = Prefs['pushover_user']
                data['title'] = "Plex Request Channel - New Movie Request"
                data['message'] = "A user has requested a new movie.\n" + title_year + "\nIMDB id: " + id + "\nPoster: " + movie['poster']
                #values = JSON.StringFromObject(data)
                response = HTTP.Request(PUSHOVER_API_URL, values=data)
                if response:
                    Log.Debug("Pushover notification sent for :" + id)
            elif type == 'tv':
                tv = Dict['tv'][id]
                data = {'token': PUSHOVER_API_KEY}
                data['user'] = Prefs['pushover_user']
                data['title'] = "Plex Request Channel - New TV Show Request"
                data['messsage'] = "A user has requested a new tv show.\n" + tv['title'] + "\nTVDB id: " + id + "\nPoster: " + tv['poster']
                #values = JSON.StringFromObject(data)
                response = HTTP.Request(PUSHOVER_API_URL, values=data)
                if response:
                    Log.Debug("Pushover notification sent for :" + id)
        except Exception as e:
            Log.Debug("Pushover failed: " + e.message)
