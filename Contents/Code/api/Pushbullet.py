import ssl
import urllib2

PUSHBULLET_API_URL = "https://api.pushbullet.com/v2/"

PUSHBULLET_API_KEY = None

def setAPI(api):
    global PUSHBULLET_API_KEY
    PUSHBULLET_API_KEY = api

def Send(title, body, channel="", device_iden=""):
    api_header = {'Authorization': 'Bearer ' + PUSHBULLET_API_KEY,
                  'Content-Type': 'application/json'
                  }
    data = {'type': 'note', 'title': title, 'body': body}
    if device_iden:
        data['device_iden'] = device_iden
    if channel:
        data['channel_tag'] = channel
    values = JSON.StringFromObject(data)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
    pushbulletrequest = urllib2.Request(PUSHBULLET_API_URL + "pushes", data=values, headers=api_header)
    return urllib2.urlopen(pushbulletrequest, context=ctx)
