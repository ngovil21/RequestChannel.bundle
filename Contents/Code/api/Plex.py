import traceback
import urllib2
import urllib2.Request

PLEX_IP = "127.0.0.1"
PLEX_PORT = "32400"


def setIp(ip):
    global PLEX_IP
    PLEX_IP = ip


def setPort(port):
    global PLEX_PORT
    PLEX_PORT = port


def getURL(secure=False):
    if PLEX_IP and PLEX_PORT:
        if secure:
            return "https://" + PLEX_IP + ":" + PLEX_PORT + "/"
        else:
            return "http://" + PLEX_IP + ":" + PLEX_PORT + "/"


def getSections(secure=False, headers={}):
    return XML.ElementFromURL(url=getURL(secure) + "library/sections", headers=headers)


# search library for query and return xml
def searchLibrary(query, local=1, secure=False, headers={}):
    try:
        return XML.ElementFromURL(url=getURL(secure) + "search?local=" + str(local) + "&query=" + String.Quote(query),
                                  headers=headers)
    except Exception as e:
        Log.Debug("Error in searchLibrary: " + e.message)
        Log.Error(str(traceback.format_exc()))  # raise last error


# try to match a movie locally in plex using title and year
def matchMovie(title, year, local=1, secure=False, headers={}):
    search = searchLibrary(title, local, secure, headers)
    matches = []
    if search:
        videos = search.xpath("//Video")
        for video in videos:
            if video.attrib['title'].lower() == title.lower() and video.attrib['year'] == year and video.attrib[
                'type'] == 'movie':
                matches.append(video.attrib['ratingKey'])
    return matches


# add a movie to a collection, requires library key and rating key
def addCollection(library_key, rating_key, collection_name, headers={}):
    data = {
        "type": 1,
        "id": rating_key,
        "collection[0].tag.tag": collection_name
    }

    try:
        req = urllib2.Request(url=getURL() + "library/sections/%s/all" % library_key, data=data, headers=headers)
        req.get_method = lambda: 'PUT'
        urllib2.urlopen(req)
    except Exception as e:
        Log.Debug("Error in addCollection: " + e.message)
        Log.Error(str(traceback.format_exc()))  # raise last error


########################################################################################################################
########################################################################################################################
################ PLEX.TV FUNCTIONS #####################################################################################
########################################################################################################################
########################################################################################################################

def getPlexTVUser(token):
    url = "https://plex.tv"
    try:
        xml = XML.ObjectFromURL(url, headers={'X-Plex-Token': token})
        plexTVUser = xml.get("myPlexUsername")
        return plexTVUser
    except:
        return None
