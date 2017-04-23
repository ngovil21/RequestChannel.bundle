OMDB_API_URL = "http://www.omdbapi.com/"

def Search(query):
    request = JSON.ObjectFromURL(url=OMDB_API_URL + "?s=" + query + "&r=json")
    if 'Search' in request:
        return request['Search']
