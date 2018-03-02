import traceback

TELEGRAM_API_URL = "https://api.telegram.org/bot"

TELEGRAM_API_KEY = ""


def getAPIURL(func):
    return TELEGRAM_API_URL + TELEGRAM_API_KEY + "/" + func


def setAPI(api):
    global TELEGRAM_API_KEY
    TELEGRAM_API_KEY = api


def getMe():
    try:
        return JSON.ObjectFromURL(getAPIURL("getMe"))
    except Exception as e:
        Log.Debug("Error in getMe: " + e.message)
        Log.Error(str(traceback.format_exc()))  # raise last error
    return


def send(chat_id, text, parse_mode='HTML', disable_notification=False):
    data = {'chat_id': chat_id, 'text': text, 'parse_mode': parse_mode, 'disable_notification': disable_notification}
    try:
        return JSON.ObjectFromURL(getAPIURL("sendMessage"), values=data)
    except Exception as e:
        Log.Debug("Error in send: " + e.message)
        Log.Error(str(traceback.format_exc()))  # raise last error
    return

