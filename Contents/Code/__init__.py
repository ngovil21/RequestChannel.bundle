TITLE    = 'Plex Request Channel'
PREFIX   = '/video/plexrequestchannel'

ART      = 'art-default.jpg'
ICON     = 'icon-default.png'

DATA_FILE = "Requests"

TMDB_API_KEY = "096c49df1d0974ee573f0295acb9e3ce"
TMDB_API_URL = "http://api.themoviedb.org/3/"
TMDB_IMAGE_BASE_URL = "http://image.tmdb.org/t/p/w500"

  
def Start():

  ObjectContainer.title1 = TITLE
  ObjectContainer.art = R(ART)

  DirectoryObject.thumb = R(ICON)
  DirectoryObject.art = R(ART)
  EpisodeObject.thumb = R(ICON)
  EpisodeObject.art = R(ART)
  VideoClipObject.thumb = R(ICON)
  VideoClipObject.art = R(ART)

  # If no Requests file exists, create it
  # The request file will be where user requests will be stored
  # if not Data.Exists(DATA_FILE):
  #   xml = XML.Element(DATA_FILE)
  #   Data.Save(DATA_FILE,xml)

###################################################################################################
# This tells Plex how to list you in the available channels and what type of channels this is 
@handler(PREFIX, TITLE, art=ART, thumb=ICON)

def MainMenu():

  oc = ObjectContainer()

  oc.add(DirectoryObject(key=Callback(AddNewMovie, title="Request a Movie"), title="Request a Movie"))
  oc.add(DirectoryObject(key=Callback(AddNewTVShow, title="Request a TV Show"), title="Request a TV Show"))
  oc.add(DirectoryObject(key=Callback(ViewRequests, title="View Requests"), title="View Requests"))

  return oc


@route(PREFIX + '/addnewmovie')
def AddNewMovie(title):
  oc = ObjectContainer()

  oc.add(InputDirectoryObject(key=Callback(SearchMovie, title="Search Results"), title=title, prompt="Enter the name or IMDB id of the movie:"))
  return oc

@route(PREFIX + '/searchmovie')
def SearchMovie(title,query):
  oc = ObjectContainer()
  query = String.Quote(query, usePlus=True)
  headers = {
      'Accept': 'application/json'
  }
  request = JSON.ObjectFromURL(url=TMDB_API_URL + "search/movie?api_key="+TMDB_API_KEY+"?query="+query, headers=headers)
  Log.Debug(JSON.StringFromObject(request))
  results = request['results']
  for key in results:
      oc.add(DirectoryObject(key=None, title=key['title']), thumb=R(TMDB_IMAGE_BASE_URL + key['post_path']))
  return oc

@route(PREFIX + '/addtvshow')
def AddNewTVShow(title):
  oc = ObjectContainer()

 # oc.add(InputDirectoryObject(key=Callback(SearchMovie, title="Search Results"), title=title, prompt="Enter the name or IMDB id of the movie:"))
  return oc

@route(PREFIX + '/viewrequests')
def ViewRequests(title):
  oc = ObjectContainer()

 # oc.add(InputDirectoryObject(key=Callback(SearchMovie, title="Search Results"), title=title, prompt="Enter the name or IMDB id of the movie:"))
  return oc
