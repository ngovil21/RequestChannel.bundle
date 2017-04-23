PUSHALOT_API_URL = "https://pushalot.com/api/sendmessage"

PUSHOVER_API_KEY = None

def setAPI(api):
    global PUSHOVER_API_KEY
    PUSHOVER_API_KEY = api

def sendPushalot(title, message, isimportant=False, isSilent=False):
    data = {'AuthorizationToken': PUSHOVER_API_KEY, 'Title': title, 'Body': message, 'IsImportant': isimportant,
            'IsSilent': isSilent}
    try:
        return HTTP.Request(PUSHALOT_API_URL, values=data)
    except Exception as e:
        Log.Debug("Error in sendPushalot: " + e.message)
        Log.Error(str(traceback.format_exc()))  # raise last error
    return None

