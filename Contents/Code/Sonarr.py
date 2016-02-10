# Sonarr Methods
import Channel
from Keyboard import Keyboard, DUMB_KEYBOARD_CLIENTS, NO_MESSAGE_CONTAINER_CLIENTS
import Requests


@route(Channel.PREFIX + '/sendtosonarr')
def SendToSonarr(tvdbid, locked='unlocked'):
    if not Prefs['sonarr_url'].startswith("http"):
        sonarr_url = "http://" + Prefs['sonarr_url']
    else:
        sonarr_url = Prefs['sonarr_url']
    if not sonarr_url.endswith("/"):
        sonarr_url += "/"
    title = Dict['tv'][series_id]['title']
    api_header = {
        'X-Api-Key': Prefs['sonarr_api']
    }
    series_id = ShowExists(tvdbid)
    if series_id:
        Dict['tv'][tvdbid]['automated'] = True
        return ManageSonarrShow(series_id=series_id, locked=locked, callback=Callback(Requests.ViewRequest, req_id=tvdbid, type='tv', locked=locked))
    lookup_json = JSON.ObjectFromURL(sonarr_url + "api/Series/Lookup?term=tvdbid:" + series_id, headers=api_header)
    found_show = None
    for show in lookup_json:
        if show['tvdbId'] == series_id:
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
    options = {'title': found_show['title'], 'tvdbId': found_show['tvdbId'], 'qualityProfileId': int(profile_id),
               'titleSlug': found_show['titleSlug'], 'rootFolderPath': rootFolderPath, 'seasons': found_show['seasons'], 'monitored': True}

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
        options['seasons'][len(options['seasons']) - 1]['monitored'] = True
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
        HTTP.Request(sonarr_url + "api/Series", data=values, headers=api_header)
        if Client.Platform in NO_MESSAGE_CONTAINER_CLIENTS or Client.Product in NO_MESSAGE_CONTAINER_CLIENTS:
            oc = ObjectContainer(title1="Sonarr", title2="Success")
        else:
            oc = ObjectContainer(header=Channel.TITLE, message="Show has been sent to Sonarr.")
        Dict['tv'][series_id]['automated'] = True
    except:
        if Client.Platform in NO_MESSAGE_CONTAINER_CLIENTS or Client.Product in NO_MESSAGE_CONTAINER_CLIENTS:
            oc = ObjectContainer(title1="Sonarr", title2="Send Failed")
        else:
            oc = ObjectContainer(header=Channel.TITLE, message="Could not send show to Sonarr!")
    if checkAdmin():
        oc.add(DirectoryObject(key=Callback(Requests.ConfirmDeleteRequest, req_id=series_id, req_type='tv', title_year=title, locked=locked),
                               title="Delete Request"))
    oc.add(DirectoryObject(key=Callback(Requests.ViewRequests, locked=locked), title="Return to View Requests"))
    oc.add(DirectoryObject(key=Callback(Channel.CMainMenu, locked=locked), title="Return to Main Menu"))
    return oc


@route(Channel.PREFIX + '/managesonarr')
def ManageSonarr(locked='unlocked'):
    oc = ObjectContainer(title1=Channel.TITLE, title2="Manage Sonarr")
    if not Prefs['sonarr_url'].startswith("http"):
        sonarr_url = "http://" + Prefs['sonarr_url']
    else:
        sonarr_url = Prefs['sonarr_url']
    if sonarr_url.endswith("/"):
        sonarr_url = sonarr_url[:-1]
    api_header = {
        'X-Api-Key': Prefs['sonarr_api']
    }
    try:
        shows = JSON.ObjectFromURL(sonarr_url + "/api/Series", headers=api_header)
    except Exception as e:
        Log.Debug(e.message)
        return MessageContainer(header=Channel.TITLE, message="Error retrieving Sonarr Shows")
    for show in shows:
        poster = None
        for image in show['images']:
            if image['coverType'] == 'poster':
                poster = sonarr_url + image['url'][image['url'].find('/MediaCover/'):]
        oc.add(TVShowObject(key=Callback(ManageSonarrShow, series_id=show['id'], title=show['title'], locked=locked), rating_key=show['tvdbId'],
                            title=show['title'], thumb=poster, summary=show['overview']))

    oc.add(DirectoryObject(key=Callback(Channel.CMainMenu, locked=locked), title="Return to Main Menu"))
    return oc


@route(Channel.PREFIX + '/managesonarrshow')
def ManageSonarrShow(series_id, title="", locked='unlocked', callback=None):
    if not Prefs['sonarr_url'].startswith("http"):
        sonarr_url = "http://" + Prefs['sonarr_url']
    else:
        sonarr_url = Prefs['sonarr_url']
    if sonarr_url.endswith("/"):
        sonarr_url = sonarr_url[:-1]
    api_header = {
        'X-Api-Key': Prefs['sonarr_api']
    }
    try:
        show = JSON.ObjectFromURL(sonarr_url + "/api/Series/" + series_id, headers=api_header)
    except Exception as e:
        Log.Debug(e.message)
        return MessageContainer(header=Channel.TITLE, message="Error retrieving Sonarr Show: " + title)
    oc = ObjectContainer(title1="Manage Sonarr Show", title2=show['title'])
    oc.add(DirectoryObject(key=Callback(SonarrMonitorShow, series_id=series_id, seasons='all', locked=locked, callback=callback), title="Monitor All Seasons"))
    # Log.Debug(show['seasons'])
    for season in show['seasons']:
        season_number = int(season['seasonNumber'])
        mark = "* " if season['monitored'] else ""
        oc.add(DirectoryObject(key=Callback(SonarrManageSeason, series_id=series_id, season=season_number, locked=locked),
                               title=mark + ("Season " + str(season_number) if season_number > 0 else "Specials"), summary=show['overview']))
    return oc


@route(Channel.PREFIX + '/sonarrmanageseason')
def SonarrManageSeason(series_id, season, locked='unlocked', callback=None):
    if not Prefs['sonarr_url'].startswith("http"):
        sonarr_url = "http://" + Prefs['sonarr_url']
    else:
        sonarr_url = Prefs['sonarr_url']
    if sonarr_url.endswith("/"):
        sonarr_url = sonarr_url[:-1]
    api_header = {
        'X-Api-Key': Prefs['sonarr_api']
    }
    oc = ObjectContainer(title1="Manage Season", title2="Season " + str(season))
    oc.add(DirectoryObject(key=Callback(SonarrMonitorShow, series_id=series_id, seasons=str(season), locked=locked, callback=callback), title="Get All Episodes"))
    # data = JSON.StringFromObject({'seriesId': series_id})
    episodes = JSON.ObjectFromURL(sonarr_url + "/api/Episode/?seriesId=" + str(series_id), headers=api_header)
    # Log.Debug(JSON.StringFromObject(episodes))
    for episode in episodes:
        if not episode['seasonNumber'] == int(season):
            continue
        oc.add(DirectoryObject(key=Callback(SonarrMonitorShow, series_id=series_id, seasons=str(season), episodes=str(episode['id'])),
                               title=str(episode['episodeNumber']) + ". " + episode['title'], summary=episode['overview']))
    return oc


@route(Channel.PREFIX + '/sonarrmonitorshow')
def SonarrMonitorShow(series_id, seasons, episodes='all', locked='unlocked', callback=None):
    if not Prefs['sonarr_url'].startswith("http"):
        sonarr_url = "http://" + Prefs['sonarr_url']
    else:
        sonarr_url = Prefs['sonarr_url']
    if sonarr_url.endswith("/"):
        sonarr_url = sonarr_url[:-1]
    api_header = {
        'X-Api-Key': Prefs['sonarr_api']
    }
    try:
        show = JSON.ObjectFromURL(sonarr_url + "/api/series/" + series_id, headers=api_header)
    except Exception as e:
        Log.Debug(e.message)
        return MessageContainer(header=Channel.TITLE, message="Error retrieving Sonarr Show: " + title)
    if seasons == 'all':
        for s in show['seasons']:
            s['monitored'] = True
        data = JSON.StringFromObject(show)
        data2 = JSON.StringFromObject({'seriesId': int(series_id)})
        try:
            HTTP.Request(url=sonarr_url + "/api/series/", data=data, headers=api_header, method='PUT')  # Post Series to monitor
            HTTP.Request(url=sonarr_url + "/api/command/SeriesSearch/", data=data2, headers=api_header)  # Search for all episodes in series
        except Exception as e:
            Log.Debug("Sonarr Monitor failed: " + Log.Debug(Response.Status) + " - " + e.message)
    else:
        if episodes == 'all':
            season_list = seasons.split()
            for s in show['seasons']:
                if str(s['seasonNumber']) in season_list:
                    s['monitored'] = True
            data = JSON.StringFromObject(show)
            try:
                HTTP.Request(sonarr_url + "/api/series", data=data, headers=api_header, method='PUT')  # Post seasons to monitor
                for s in season_list:  # Search for each chosen season
                    data2 = JSON.StringFromObject({'seriesId': int(series_id), 'seasonNumber': int(s)})
                    HTTP.Request(sonarr_url + "/api/command/SeasonSearch", headers=api_header, data=data2)
            except Exception as e:
                Log.Debug("Sonarr Monitor failed: " + e.message)
        else:
            episode_list = episodes.split()
            try:
                for e in episode_list:
                    episode = JSON.ObjectFromURL(sonarr_url + "/api/Episode/" + str(e), headers=api_header)
                    episode['monitored'] = True
                    data = JSON.StringFromObject(episode)
                    HTTP.Request(sonarr_url + "/api/Episode/" + str(e), data=data, headers=api_header, method='PUT')
                data2 = JSON.StringFromObject({'name': "EpisodeSearch", 'episodeIds': episode_list})
                HTTP.Request(sonarr_url + "/api/command", headers=api_header, data=data2)
            except Exception as e:
                Log.Debug("Sonarr Monitor failed: " + e.message)
            return SonarrManageSeason(series_id=series_id, season=seasons, locked=locked)
    if callback:
        oc = ObjectContainer(title1="Sonarr Submit", title2="Success", message="Sucessfully sent to Sonarr")
        if Client.Platform in NO_MESSAGE_CONTAINER_CLIENTS or Client.Product in NO_MESSAGE_CONTAINER_CLIENTS:
            oc.message = None
        oc.add(DirectoryObject(key=callback, title="Go Back"))
        oc.add(DirectoryObject(key=Callback(Channel.CMainMenu, locked=locked), title="Return to Main Menu"))
        return oc
    return Channel.CMainMenu(locked=locked)


def ShowExists(tvdbid):
    if not Prefs['sonarr_url'].startswith("http"):
        sonarr_url = "http://" + Prefs['sonarr_url']
    else:
        sonarr_url = Prefs['sonarr_url']
    if not sonarr_url.endswith("/"):
        sonarr_url += "/"
    api_header = {
        'X-Api-Key': Prefs['sonarr_api']
    }
    series = JSON.ObjectFromURL(sonarr_url + "api/Series", headers=api_header)
    for show in series:
        if show['tvdbId'] == int(tvdbid) and show['id']:
            return show['id']
    return False
