PUSHALOT_API_URL = "https://pushalot.com/api/sendmessage"

PUSHALOT_API_KEY = None

def setAPI(api):
    global PUSHALOT_API_KEY
    PUSHALOT_API_KEY = api

def send(title, message, isimportant=False, isSilent=False):
    data = {'AuthorizationToken': PUSHALOT_API_KEY, 'Title': title, 'Body': message, 'IsImportant': isimportant,
            'IsSilent': isSilent}
    try:
        return HTTP.Request(PUSHALOT_API_URL, values=data)
    except Exception as e:
        Log.Debug("Error in sending Pushalot: " + e.message)
        Log.Error(str(traceback.format_exc()))  # raise last error
    return None

