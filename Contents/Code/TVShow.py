#TVShow Functions

from Channel import MainMenu, PREFIX, TITLE
from Keyboard import Keyboard, DUMB_KEYBOARD_CLIENTS, NO_MESSAGE_CONTAINER_CLIENTS
from Sonarr import SendToSonarr
from Sickbeard import SendToSickbeard
from Notifications import notifyRequest

### URL Constants for TheTVDB ##########################
TVDB_API_KEY = "B93EF22D769A70CB"
TVDB_API_URL = "http://thetvdb.com/api/"
TVDB_BANNER_URL = "http://thetvdb.com/banners/"
#######################################################


@route(PREFIX + '/addtvshow')
def AddNewTVShow(title="Request a TV Show", locked='unlocked'):
    token = Request.Headers['X-Plex-Token']
    if Prefs['weekly_limit'] and int(Prefs['weekly_limit'] > 0) and not checkAdmin():
        if token in Dict['register'] and Dict['register'][token]['requests'] >= int(Prefs['weekly_limit']):
            return MainMenu(message="Sorry you have reached your weekly request limit of " + Prefs['weekly_limit'] + ".", locked=locked,
                            title1="Main Menu", title2="Weekly Limit")
    if token in Dict['blocked']:
        return MainMenu(message="Sorry you have been blocked.", locked=locked,
                        title1="Main Menu", title2="User Blocked")
    if Client.Platform == "iOS" or Client.Product == "Plex for iOS":
        oc = ObjectContainer(title2=title)
    else:
        oc = ObjectContainer(header=TITLE, message="Please enter the name of the TV Show in the search box and press enter.")
    if Client.Product in DUMB_KEYBOARD_CLIENTS or Client.Platform in DUMB_KEYBOARD_CLIENTS:
        Log.Debug("Client does not support Input. Using DumbKeyboard")
        # DumbKeyboard(prefix=PREFIX, oc=oc, callback=SearchTV, dktitle="Request a TV Show", dkthumb=R('search.png'), locked=locked)
        oc.add(DirectoryObject(key=Callback(Keyboard, callback=SearchTV, parent=MainMenu, locked=locked), title="Request a TV Show",
                               thumb=R('search.png')))
    else:
        oc.add(InputDirectoryObject(key=Callback(SearchTV, locked=locked), title="Request a TV Show", prompt="Enter the name of the TV Show:",
                                    thumb=R('search.png')))
    return oc


@route(PREFIX + '/searchtv')
def SearchTV(query, locked='unlocked'):
    oc = ObjectContainer(title1="Search Results", title2=query, content=ContainerContent.Shows, view_group="Details")
    query = String.Quote(query, usePlus=True)
    xml = XML.ElementFromURL(TVDB_API_URL + "GetSeries.php?seriesname=" + query)
    series = xml.xpath("//Series")
    if len(series) == 0:
        if Client.Platform in NO_MESSAGE_CONTAINER_CLIENTS or Client.Product in NO_MESSAGE_CONTAINER_CLIENTS:
            oc = ObjectContainer(title2="No Results")
        else:
            oc = ObjectContainer(header=TITLE, message="Sorry there were no results found.")
        if Client.Product in DUMB_KEYBOARD_CLIENTS or Client.Platform in DUMB_KEYBOARD_CLIENTS:
            Log.Debug("Client does not support Input. Using DumbKeyboard")
            # DumbKeyboard(prefix=PREFIX, oc=oc, callback=SearchTV, dktitle="Search Again", dkthumb=R('search.png'), locked=locked)
            oc.add(DirectoryObject(key=Callback(Keyboard, callback=SearchTV, parent=MainMenu, locked=locked), title="Search Again",
                                   thumb=R('search.png')))
        else:
            oc.add(InputDirectoryObject(key=Callback(SearchTV, locked=locked), title="Search Again", prompt="Enter the name of the TV Show:",
                                        thumb=R('search.png')))
        oc.add(DirectoryObject(key=Callback(MainMenu, locked=locked), title="Return to Main Menu", thumb=R('return.png')))
        return oc
    count = 0
    for serie in series:
        series_id = ""
        title = ""
        year = ""
        poster = ""
        summary = ""
        for child in serie.getchildren():
            if child.tag.lower() == "seriesid" and child.text:
                series_id = child.text
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
        if count < 11:  # Let's look for the actual poster for only the first 10 tv shows to reduce api hits
            try:
                serie_page = XML.ElementFromURL(TVDB_API_URL + TVDB_API_KEY + "/series/" + series_id)
                poster_text = serie_page.xpath("//Series/poster/text()")
                if poster_text:
                    poster = TVDB_BANNER_URL + poster_text[0]
            except Exception as e:
                Log.Debug(e)
            count += 1
        if series_id == "":
            Log.Debug("No id found!")
        if year:
            title_year = title + " (" + year + ")"
        else:
            title_year = title
        if poster:
            thumb = poster
        else:
            thumb = R('no-poster.jpg')
        oc.add(
            TVShowObject(
                key=Callback(ConfirmTVRequest, series_id=series_id, source='tvdb', title=title, year=year, poster=poster, summary=summary,
                             locked=locked),
                rating_key=series_id, title=title_year, summary=summary, thumb=thumb))
    if Client.Product in DUMB_KEYBOARD_CLIENTS or Client.Platform in DUMB_KEYBOARD_CLIENTS:
        Log.Debug("Client does not support Input. Using DumbKeyboard")
        # DumbKeyboard(prefix=PREFIX, oc=oc, callback=SearchTV, dktitle="Search Again", dkthumb=R('search.png'), locked=locked)
        oc.add(
            DirectoryObject(key=Callback(Keyboard, callback=SearchTV, parent=MainMenu, locked=locked), title="Search Again", thumb=R('search.png')))
    else:
        oc.add(InputDirectoryObject(key=Callback(SearchTV, locked=locked), title="Search Again", prompt="Enter the name of the TV Show:",
                                    thumb=R('search.png')))
    oc.add(DirectoryObject(key=Callback(MainMenu, locked=locked), title="Return to Main Menu", thumb=R('return.png')))
    return oc


@route(PREFIX + '/confirmtvrequest')
def ConfirmTVRequest(series_id, title, source="", year="", poster="", backdrop="", summary="", locked='unlocked'):
    if year:
        title_year = title + " " + "(" + year + ")"
    else:
        title_year = title

    if Client.Platform == "iOS" or Client.Product == "Plex for iOS":
        oc = ObjectContainer(title1="Confirm TV Request", title2=title_year + "?")
    else:
        oc = ObjectContainer(title1="Confirm TV Request", title2="Are you sure you would like to request the TV Show " + title_year + "?",
                             header=TITLE, message="Request tv show " + title_year + "?")

    found_match = False
    try:
        local_search = XML.ElementFromURL(url="http://127.0.0.1:32400/search?local=1&query=" + String.Quote(title), headers=Request.Headers)
        if local_search:
            # Log.Debug(XML.StringFromElement(local_search))
            videos = local_search.xpath("//Directory")
            for video in videos:
                video_attr = video.attrib
                if video_attr['title'] == title and video_attr['year'] == year and video_attr['type'] == 'show':
                    Log.Debug("Possible match found: " + str(video_attr['ratingKey']))
                    summary = "(In Library: " + video_attr['librarySectionTitle'] + ") " + (video_attr['summary'] if video_attr['summary'] else "")
                    oc.add(
                        TVShowObject(key=Callback(MainMenu, locked=locked, message="TV Show already in library.", title1="In Library", title2=title),
                                     rating_key=video_attr['ratingKey'], title="+ " + title, summary=summary, thumb=video_attr['thumb']))
                    found_match = True
                    break
    except:
        pass

    if found_match:
        if Client.Platform in NO_MESSAGE_CONTAINER_CLIENTS or Client.Product in NO_MESSAGE_CONTAINER_CLIENTS:
            oc.title1 = "Show Already Exists"
        else:
            oc.message = "TV Show appears to already exist in the library. Are you sure you would still like to request it?"
    if not found_match and Client.Platform == ClientPlatform.Android:  # If an android, add an empty first item because it gets truncated for some reason
        oc.add(DirectoryObject(key=None, title=""))
    oc.add(DirectoryObject(
        key=Callback(AddTVRequest, series_id=series_id, source=source, title=title, year=year, poster=poster, backdrop=backdrop, summary=summary,
                     locked=locked), title="Add Anyways" if found_match else "Yes", thumb=R('check.png')))
    oc.add(DirectoryObject(key=Callback(MainMenu, locked=locked), title="No", thumb=R('x-mark.png')))

    return oc


@indirect
@route(PREFIX + '/addtvrequest')
def AddTVRequest(series_id, title, source='', year="", poster="", backdrop="", summary="", locked='unlocked'):
    if series_id in Dict['tv']:
        Log.Debug("TV Show is already requested")
        return MainMenu(locked=locked, message="TV Show has already been requested", title1=title, title2="Already Requested")
    else:
        token = Request.Headers['X-Plex-Token']
        user = ""
        if token in Dict['register'] and Dict['register'][token]['nickname']:
            user = Dict['register'][token]['nickname']
            Dict['register'][token]['requests'] = Dict['register'][token]['requests'] + 1
        Dict['tv'][series_id] = {'type': 'tv', 'id': series_id, 'source': source, 'title': title, 'year': year, 'poster': poster,
                                 'backdrop': backdrop, 'summary': summary, 'user': user, 'automated': False}
        Dict.Save()
        if Prefs['sonarr_autorequest'] and Prefs['sonarr_url'] and Prefs['sonarr_api']:
            SendToSonarr(tvdbid=series_id)
        if Prefs['sickbeard_autorequest'] and Prefs['sickbeard_url'] and Prefs['sickbeard_api']:
            SendToSickbeard(series_id)
        notifyRequest(req_id=series_id, req_type='tv')
        return MainMenu(locked=locked, message="TV Show has been requested", title1=title, title2="Requested")