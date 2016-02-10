#CouchPotato Functions
import Channel
from Keyboard import Keyboard, DUMB_KEYBOARD_CLIENTS, NO_MESSAGE_CONTAINER_CLIENTS
import Requests
import Movie


@route(Channel.PREFIX + '/sendtocouchpotato')
def SendToCouchpotato(movie_id, locked='unlocked'):
    if movie_id not in Dict['movie']:
        return MessageContainer("Error", "The movie id was not found in the database")
    movie = Dict['movie'][movie_id]
    if 'source' in movie and movie['source'] == 'tmdb':  # Check if id source is tmdb
        # we need to convert tmdb id to imdb
        json = JSON.ObjectFromURL(Movie.TMDB_API_URL + "movie/" + movie_id + "?api_key=" + Movie.TMDB_API_KEY, headers={'Accept': 'application/json'})
        if 'imdb_id' in json and json['imdb_id']:
            imdb_id = json['imdb_id']
        else:
            imdb_id = ""
            if Client.Platform in NO_MESSAGE_CONTAINER_CLIENTS or Client.Product in NO_MESSAGE_CONTAINER_CLIENTS:
                oc = ObjectContainer(title1="CouchPotato", title2="Send Failed")
            else:
                oc = ObjectContainer(header=Channel.TITLE, message="Unable to get IMDB id for movie, add failed...")
            oc.add(DirectoryObject(key=Callback(Requests.ViewRequests, locked=locked), title="Return to View Requests"))
            return oc
    else:  # Assume we have an imdb_id by default
        imdb_id = movie_id
    # we have an imdb id, add to couchpotato
    if not Prefs['couchpotato_url'].startswith("http"):
        couchpotato_url = "http://" + Prefs['couchpotato_url']
    else:
        couchpotato_url = Prefs['couchpotato_url']
    if not couchpotato_url.endswith("/"):
        couchpotato_url += "/"
    values = {'identifier': imdb_id}
    if Prefs['couchpotato_profile']:
        cat = JSON.ObjectFromURL(couchpotato_url + "api/" + Prefs['couchpotato_api'] + "/profile.list/")
        if cat['success']:
            for key in cat['list']:
                if key['label'] == Prefs['couchpotato_profile']:
                    values['profile_id'] = key['_id']
        else:
            Log.Debug("Unable to open up Couchpotato Profile List")
    if Prefs['couchpotato_category']:
        cat = JSON.ObjectFromURL(couchpotato_url + "api/" + Prefs['couchpotato_api'] + "/category.list/")
        if cat['success']:
            for key in cat['categories']:
                if key['label'] == Prefs['couchpotato_category']:
                    values['category_id'] = key['_id']
        else:
            Log.Debug("Unable to open up Couchpotato Category List")
    try:
        json = JSON.ObjectFromURL(couchpotato_url + "api/" + Prefs['couchpotato_api'] + "/movie.add/", values=values)
        if 'success' in json and json['success']:
            if Client.Platform in NO_MESSAGE_CONTAINER_CLIENTS or Client.Product in NO_MESSAGE_CONTAINER_CLIENTS:
                oc = ObjectContainer(title1="Couchpotato", title2="Success")
            else:
                oc = ObjectContainer(header=Channel.TITLE, message="Movie Request Sent to CouchPotato!")
            Dict['movie'][movie_id]['automated'] = True
        else:
            if Client.Platform in NO_MESSAGE_CONTAINER_CLIENTS or Client.Product in NO_MESSAGE_CONTAINER_CLIENTS:
                oc = ObjectContainer(title1="CouchPotato", title2="Send Failed")
            else:
                oc = ObjectContainer(header=Channel.TITLE, message="CouchPotato Send Failed!")
    except:
        if Client.Platform in NO_MESSAGE_CONTAINER_CLIENTS or Client.Product in NO_MESSAGE_CONTAINER_CLIENTS:
            oc = ObjectContainer(title1="CouchPotato", title2="Send Failed")
        else:
            oc = ObjectContainer(header=Channel.TITLE, message="CouchPotato Send Failed!")
    key = Dict['movie'][movie_id]
    title_year = key['title'] + " (" + key['year'] + ")"
    if Channel.checkAdmin():
        oc.add(DirectoryObject(key=Callback(Requests.ConfirmDeleteRequest, req_id=movie_id, req_type='movie', title_year=title_year, locked=locked),
                               title="Delete Request"))
    oc.add(DirectoryObject(key=Callback(Requests.ViewRequests, locked=locked), title="Return to View Requests"))
    return oc
