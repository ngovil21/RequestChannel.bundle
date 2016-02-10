#Sickbeard Functions


@route(Channel.PREFIX + "/sendtosickbeard")
def SendToSickbeard(series_id, locked='unlocked'):
    # return ViewRequests(locked=locked, message="Sorry, Sickbeard is not available yet.")
    if not Prefs['sickbeard_url'].startswith("http"):
        sickbeard_url = "http://" + Prefs['sickbeard_url']
    else:
        sickbeard_url = Prefs['sickbeard_url']
    if not sickbeard_url.endswith("/"):
        sickbeard_url += "/"
    title = Dict['tv'][series_id]['title']
    data = dict(cmd='show.addnew', tvdbid=series_id)

    use_sickrage = (Prefs['sickbeard_sickrage'] == 'SickRage')

    if Prefs['sickbeard_location']:
        data['location'] = Prefs['sickbeard_location']
    if Prefs['sickbeard_status']:
        data['status'] = Prefs['sickbeard_status']
    if Prefs['sickbeard_initial']:
        data['initial'] = Prefs['sickbeard_initial']
    if Prefs['sickbeard_archive']:
        data['archive'] = Prefs['sickbeard_archive']
    if Prefs['sickbeard_langauge'] or use_sickrage:
        data['lang'] = Prefs['sickbeard_language'] if Prefs['sickbeard_language'] else "en"  # SickRage requires lang set

    if use_sickrage:
        data['anime'] = False  # SickRage requires anime set

    # Log.Debug(str(data))

    try:
        resp = JSON.ObjectFromURL(sickbeard_url + "api/" + Prefs['sickbeard_api'], values=data)
        # Log.Debug(JSON.StringFromObject(resp))
        if 'success' in resp and resp['success']:
            if Client.Platform in NO_MESSAGE_CONTAINER_CLIENTS or Client.Product in NO_MESSAGE_CONTAINER_CLIENTS:
                oc = ObjectContainer(title1=Prefs['sickbeard_sickrage'], title2="Success")
            else:
                oc = ObjectContainer(header=Channel.TITLE, message="Show added to " + Prefs['sickbeard_sickrage'])
            Dict['tv'][series_id]['automated'] = True
        else:
            if Client.Platform in NO_MESSAGE_CONTAINER_CLIENTS or Client.Product in NO_MESSAGE_CONTAINER_CLIENTS:
                oc = ObjectContainer(title1=Prefs['sickbeard_sickrage'], title2="Error")
            else:
                oc = ObjectContainer(header=Channel.TITLE, message="Could not add show to " + Prefs['sickbeard_sickrage'])
    except Exception as e:
        oc = ObjectContainer(header=Channel.TITLE, message="Could not add show to " + Prefs['sickbeard_sickrage'])
        Log.Debug(e.message)
    if checkAdmin():
        oc.add(DirectoryObject(key=Callback(Requests.ConfirmDeleteRequest, series_id=series_id, type='tv', title_year=title, locked=locked),
                               title="Delete Request"))
    oc.add(DirectoryObject(key=Callback(Requests.ViewRequests, locked=locked), title="Return to View Requests"))
    oc.add(DirectoryObject(key=Callback(Channel.CMainMenu, locked=locked), title="Return to Main Menu"))
    return oc
