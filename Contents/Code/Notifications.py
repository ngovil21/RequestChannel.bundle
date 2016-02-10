#Notifications Functions

# Notify user of requests
def notifyRequest(req_id, req_type, title="", message=""):
    if Prefs['pushbullet_api']:
        try:
            user = "A user"
            token = Request.Headers['X-Plex-Token']
            if token in Dict['register'] and Dict['register'][token]['nickname']:
                user = Dict['register'][token]['nickname']
            if req_type == 'movie':
                movie = Dict['movie'][req_id]
                title_year = movie['title'] + " (" + movie['year'] + ")"
                title = "Plex Request Channel - New Movie Request"
                message = user + " has requested a new movie.\n" + title_year + "\nIMDB id: " + req_id + "\nPoster: " + movie['poster']
            elif req_type == 'tv':
                tv = Dict['tv'][req_id]
                title = "Plex Request Channel - New TV Show Request"
                message = user + " has requested a new tv show.\n" + tv['title'] + "\nTVDB id: " + req_id + "\nPoster: " + tv['poster']
            else:
                return
            if Prefs['pushbullet_devices']:
                devices = Prefs['pushbullet_devices'].split(",")
                for d in devices:
                    response = sendPushBullet(title, message, d)
                    if response:
                        Log.Debug("Pushbullet notification sent to device: " + d + " for: " + req_id)
            else:
                response = sendPushBullet(title, message)
                if response:
                    Log.Debug("Pushbullet notification sent for: " + req_id)
        except Exception as e:
            Log.Debug("Pushbullet failed: " + e.message)
    if Prefs['pushover_user']:
        try:
            user = "A user"
            token = Request.Headers['X-Plex-Token']
            if token in Dict['register'] and Dict['register'][token]['nickname']:
                user = Dict['register'][token]['nickname']
            if req_type == 'movie':
                movie = Dict['movie'][req_id]
                title_year = movie['title'] + " (" + movie['year'] + ")"
                title = "Plex Request Channel - New Movie Request"
                message = user + " has requested a new movie.\n" + title_year + "\nIMDB id: " + req_id + "\nPoster: " + movie['poster']
            elif req_type == 'tv':
                tv = Dict['tv'][req_id]
                title = "Plex Request Channel - New TV Show Request"
                message = user + " has requested a new tv show.\n" + tv['title'] + "\nTVDB id: " + req_id + "\nPoster: " + tv['poster']
            else:
                return
            response = sendPushover(title, message)
            if response:
                Log.Debug("Pushover notification sent for :" + req_id)
        except Exception as e:
            Log.Debug("Pushover failed: " + e.message)
    if Prefs['email_to']:
        try:
            user = "A user"
            token = Request.Headers['X-Plex-Token']
            if token in Dict['register'] and Dict['register'][token]['nickname']:
                user = Dict['register'][token]['nickname']
            if req_type == 'movie':
                movie = Dict['movie'][req_id]
                title = movie['title'] + " (" + movie['year'] + ")"
                poster = movie['poster']
                id_type = "IMDB"
                subject = "Plex Request Channel - New Movie Request"
                summary = ""
                if movie['summary']:
                    summary = movie['summary'] + "<br>\n"
            elif req_type == 'tv':
                tv = Dict['tv'][req_id]
                title = tv['title']
                id_type = "TVDB"
                poster = tv['poster']
                subject = "Plex Request Channel - New TV Show Request"
                summary = ""
                if tv['summary']:
                    summary = tv['summary'] + "<br>\n"
            else:
                return
            message = user + " has made a new request! <br><br>\n" + \
                      "<font style='font-size:20px; font-weight:bold'> " + title + " </font><br>\n" + \
                      "(" + id_type + " id: " + req_id + ") <br>\n" + \
                      summary + \
                      "<Poster:><img src= '" + poster + "' width='300'>"
            sendEmail(subject, message, 'html')
            Log.Debug("Email notification sent for: " + req_id)
        except Exception as e:
            Log.Debug("Email failed: " + e.message)


def Notify(title, body, devices=None):
    if Prefs['email_to']:
        try:
            if not sendEmail(title, body, 'html'):
                Log.Debug("Email notification sent")
        except Exception as e:
            Log.Debug("Email failed: " + e.message)
    if Prefs['pushbullet_api']:
        try:
            if devices:
                for d in devices.split(','):
                    if sendPushBullet(title, body, d):
                        Log.Debug("Pushbullet notification sent")
            elif sendPushBullet(title, body, device_iden):
                Log.Debug("Pushbullet notification sent")
        except Exception as e:
            Log.Debug("PushBullet failed: " + e.message)
    if Prefs['pushover_user']:
        try:
            if sendPushover(title, body):
                Log.Debug("Pushover notification sent")
        except Exception as e:
            Log.Debug("Pushover failed: " + e.message)


def sendPushBullet(title, body, device_iden=""):
    api_header = {'Authorization': 'Bearer ' + Prefs['pushbullet_api'],
                  'Content-Type': 'application/json'
                  }
    data = {'type': 'note', 'title': title, 'body': body}
    if device_iden:
        data['device_iden'] = device_iden
    values = JSON.StringFromObject(data)
    return HTTP.Request(PUSHBULLET_API_URL + "pushes", data=values, headers=api_header)


def sendPushover(title, message):
    data = {'token': Prefs['pushover_api'], 'user': Prefs['pushover_user'], 'title': title, 'message': message}
    return HTTP.Request(PUSHOVER_API_URL, values=data)


# noinspection PyUnresolvedReferences
def sendEmail(subject, body, email_type='html'):
    from email.MIMEText import MIMEText
    from email.MIMEMultipart import MIMEMultipart
    import smtplib

    msg = MIMEMultipart()
    msg['From'] = Prefs['email_from']
    msg['To'] = Prefs['email_to']
    msg['Subject'] = subject
    msg.attach(MIMEText(body, email_type))
    server = smtplib.SMTP(Prefs['email_server'], int(Prefs['email_port']))
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(Prefs['email_username'], Prefs['email_password'])
    text = msg.as_string()
    senders = server.sendmail(Prefs['email_from'], Prefs['email_to'], text)
    server.quit()
    return senders
