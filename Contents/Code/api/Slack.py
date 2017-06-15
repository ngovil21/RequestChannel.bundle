import traceback

SLACK_API_URL = "https://slack.com/api/"
SLACK_API = ""
SLACK_USER = ""

def setAPI(api):
    global SLACK_API
    SLACK_API = api

def setUser(user):
    global SLACK_USER
    SLACK_USER = user


def send(message, channel=None):
    data = {
        'token': SLACK_API,
        'username': SLACK_USER,
        'text': message
    }
    if channel:
        data['channel'] = channel
    try:
        return JSON.ObjectFromURL(SLACK_API_URL + "chat.postMessage", values=data)
    except Exception as e:
        Log.Debug("Error in send: " + e.message)
        Log.Error(str(traceback.format_exc()))  # raise last error
    return None
