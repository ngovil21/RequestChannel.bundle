# MOST IMPORTANT NOTE: BEFORE WRITING A CHANNEL, THERE MUST ALREADY BE A URL SERVICE FOR THE VIDEOS ON THE WEBSITE
# YOU WANT TO CREATE A CHANNEL FOR OR YOU WILL HAVE TO WRITE A URL SERVICE BEFORE YOU CAN WRITE THE CHANNEL. TO
# SEE IF A URL SERVICE ALREADY EXISTS, CHECK THE SERVICES BUNDLE IN THE PLEX PLUGIN FOLDER

# IMPORTANT NOTE: PYTHON IS VERY SENSITIVE TO PROPER INDENTIONS.  IF YOUR CHANNEL HAS IMPROPER INDENTIONS IT WILL
# NOT BE RECOGNIZED BY PLEX. I RUN THE PROGRAM THROUGH A CHECK MODULE ON A LOCAL VERSION OF PYTHON I HAVE LOADED
# PRIOR TO ACCESSING IT THROUGH PLEX TO MAKE SURE THERE ARE NO INDENTION ERRORS.

# You will need to decide how you want to set up your channel. If you want to have just one page that list all 
# the videos or if you want to break these videos down into subsections for different types of videos, individual shows, season, etc
# It is easiest to determine this system based on the structure of the website you are accessing. 

# You can hard code these choice in or pull the data from a web page or JSON data file and put it in a for loop to 
# automate the process. I created a basic example in the form of functions below to show the most common methods of 
# parsing data from different types of websites. When you want to produce results to the screen and have subpage come up # when they click on those results, you usually will use a
# DirectoryObject and include the name of the next function that will create that subpage called in the key.
# The key callback section sends your data to the next function that you will use to produce your next subpage.  Usually
# you will pass the value of the url onto your next function, but there are many attributes that can be sent.  It is good 
# to pass the title as well so it shows up at the top of the screen. Refer to the Framework Documentation to see the full
# list

# You will need a good working knowledge of xpath the parse the data properly.  Good sources for information related to 
# xpath are:
# 'http://devblog.plexapp.com/2012/11/14/xpath-for-channels-the-good-the-bad-and-the-fugly/'
# 'http://forums.plexapp.com/index.php/topic/49086-xpath-coding/'

# Here is a good article about working with Chrome Development Tools: 
# 'http://devblog.plexapp.com/2012/09/27/using-chromes-built-in-debugger-for-channel-development/'

# And here are a few pages that give you some pointers ON figuring out the basics of creating a channel
# 'http://devblog.plexapp.com/2011/11/16/a-beginners-guide-to-v2-1/'
# 'http://forums.plexapp.com/index.php/topic/28084-plex-plugin-development-walkthrough/'

# The title of your channel should be unique and as explanatory as possible.  The preifx is used for the channel
# store and shows you where the channel is executed in the log files

TITLE    = 'Plex Request Channel'
PREFIX   = '/video/plexrequestchannel'

# The images below are the default graphic for your channel and should be saved or located in you Resources folder
# The art and icon should be a certain size for channel submission. The graphics should be good quality and not be blurry
# or pixelated. Icons must be 512x512 PNG files and be named, icon-default.png. The art must be 1280x720 JPG files and be
# named, art-default.jpg. The art shows up in the background of the PMC Client, so you want to make sure image you choose 
# is not too busy or distracting.  I tested out a few in PMC to figure out which one looked best.

ART      = 'art-default.jpg'
ICON     = 'icon-default.png'

# Below you would set any other global variables you may want to use in your programming. I tend to automatically create 
# a base url for the website I am accessing to add to any urls that are returned with just the folder path and not the 
# whole url and an http for urls that are returned to the channel without these at the beginning

WebsiteURL = 'http://www.anysite.com'
http = 'http:'
# This variable it to make an id below work as a url link
WebsiteEpURL = 'http://www.anysite.com/watch/'

# These are regex variables that will be used later to search a document for ids
# it seems to work well to just put "(.?)" between the any text that appears before and after the data you 
# want to return with your regex, where "(.?)" represents the data you are trying to pull
RE_LIST_ID = Regex('listId: "(.+?)", pagesConfig: ')
RE_CONTENT_ID = Regex('CONTENT_ID = "(.+?)";')


###################################################################################################
# This (optional) function is initially called by the PMS framework to initialize the plug-in. This includes setting up
# the Plug-in static instance along with the displayed artwork. These setting below are pretty standard
# You first set up the containers and default for all possible objects.  You will probably mostly use Directory Objects
# and Videos Objects. But many of the other objects give you added entry fields you may want to use and set default thumb
# and art for. For a full list of objects and their parameters, refer to the Framework Documentation.
  
def Start():

# There are  few commands you may see appear in this section that are no longer needed.  Below is an explanation of them
# provided from a very helpful channel designer who was nice enough to explain their purpose to me:
#    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
# This a left-over from when plugins had more control over how the contents were displayed. ViewGroups were defined to 
# tell the client how to display the contents of the directory. Now, most (if not all) clients have a fairly rigid model
# for what types of content get display in which way. Generally, it is best to remove it from a plugins when since it
# gets ignored anyways. 
#
#    HTTP.CacheTime = CACHE_1HOUR
# This setting a global cache time for all HTTP requests made by the plugin. This over-rides the framework's default 
# cache period which,
# I don't remember off the top of my head. It is entirely optional, but if you're going to use it, the idea is to pick a 
# cache-time that is reasonable. Ie. store data for a long enough time that you can realistically reduce the load on
# external servers as well as speed up the load-time for HTTP-requests, but not so long that changes/additions are not
# caught in a reasonable time frame. IMO, unless you specifically want/need a specific cache-length, I would remove that
# line and allow the framework to manage the cache with its default settings.
#
#   HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:18.0) Gecko/20100101 Firefox/18.0'
# This assigning a specific User-Agent header for all HTTP requests made by the plugin. Generally speaking, each time a
# plugin is started, a user-agent is randomly selected from a list to be used for all HTTP requests. In some cases, a
# plugin will perform better using a specific user-agent instead of a randomly assigned one. For example, some websites
# return different data for Safari on an iPad, then what they return for Chrome or Firefox on a PC. Again, if you don't
# have a specific need to set a specific user-agent, I would remove that code from your channel.

# You set up the default attributes for all you object containers and objects.  You will probably mostly use Directory
# Objects and Videos Objects but many of the other objects give you added entry fields you may want to use.  For a full 
# list of objects and their parameters, refer to the Framework Documentation.

# Important Note: (R stands for Resources folder) to tell the channel where these images are located.

  ObjectContainer.title1 = TITLE
  ObjectContainer.art = R(ART)

  DirectoryObject.thumb = R(ICON)
  DirectoryObject.art = R(ART)
  EpisodeObject.thumb = R(ICON)
  EpisodeObject.art = R(ART)
  VideoClipObject.thumb = R(ICON)
  VideoClipObject.art = R(ART)

###################################################################################################
# This tells Plex how to list you in the available channels and what type of channels this is 
@handler(PREFIX, TITLE, art=ART, thumb=ICON)

# This function is the first and main menu for you channel.

def MainMenu():

# You have to open an object container to produce the icons you want to appear on this page. 
  oc = ObjectContainer()

# Below is a basic example of a list of three object containers that returns an icon to the screen with a title.
# In this version we just hardcoded in the sections we would like to break the videos into based on the types of functions
# that will be described below. I am using a function from below that pulls the thumb from the head of the page
  oc.add(DirectoryObject(key=Callback(AddNewMovie, title="Request a Movie"), title="Request a Movie", thumb=GetThumb(url='http://www.webpage1.com')))
  oc.add(DirectoryObject(key=Callback(AddNewTVShow, title="Request a TV Show"), title="Request a TV Show", thumb=GetThumb(url='http://www.webpage2.com')))
  oc.add(DirectoryObject(key=Callback(ViewRequests, title="View Requests"), title="View Requests", thumb=GetThumb(url='http://www.webpage3.com')))

  return oc


@route(PREFIX + '/addnewmovie')
def AddNewMovie(title):
  oc = ObjectContainer

  oc.add(InputDirectoryObject(key=Callback(SearchMovie, title="Search Results"), title=title, prompt="Enter the name or IMDB id of the movie:"))
  return oc

@route(PREFIX + '/searchmovie')
def SearchMovie(title,query):
  oc = ObjectContainer()
  query = String.Quote(query, usePlus=True)


  return oc

#########################################################################################################################
# the command below is helpful when looking at logs to determine which function is being executed
# ALSO SAYS IT HELPS THE DESIGNER CREATE A "REST-like API" BUT I DO NOT KNOW WHAT EXACTLY THAT MEANS. I AM THINKING IT
# ALLOWS ACCESS DIRECTLY TO THE FUNCTION FROM OUTSIDE OF THE CODE
@route(PREFIX + '/showrss')

# This function shows a basic loop to go through an xml rss feed and pull the data for all the videos or shows listed
# there
def VideoRSS(title):

# define an object container and pass the title in from the function above
  oc = ObjectContainer(title2=title)
  
# This is the data parsing API to pull elements from an RSS feed. 
  xml = RSS.FeedFromURL(url)
# enter a for loop to return an object for every entry in the feed
  for item in xml.entries:
# Pull the data that is available in the form of link, title, date and description
    url = item.link
    title = item.title
    # The date is not always in the correct format so it is always best to return use Datetime.ParseDate to make sure it is correct 
    date = Datetime.ParseDate(item.date)
    desc = item.description
    # Return an object for each item you loop through.  This produces an icon or video name for each entry to the screen.
    # It is important to ensure you are reading these attributes in to the correct name.  See the Framework Documentation 
    # for a complete list of objects and the attributes that can be returned with each.
    oc.add(
      VideoClipObject(
	url = url, 
	title = title, 
	summary = description, 
	# Resource.ContentsOfURLWithFallback test the icon to make sure it is valid or returns the fallback if not
	thumb = Resource.ContentsOfURLWithFallback(thumb, fallback=R(ICON)), 
	originally_available_at = date
	)
      )

# This code below is helpful to show when a source is empty
  if len(oc) < 1:
    Log ('still no value for objects')
    return ObjectContainer(header="Empty", message="Unable to display videos for this show right now.")      

  return oc

#################################################################################################################
# This function is an example of parsing data from a html page
@route(PREFIX + '/showhtml')
def ShowHTML(title):


# The parsing API is followed by .xpath(Ô//PARENTELEMENTÕ): where PARENTELEMENT is the parent element within the XML document for  
# which you want to return data values to the variables for the videos. For example each video in your RSS feed may be contained 
# within an Item element tag that has element tags for title, thumbnail, description, etc.

# Open the object container
  oc = ObjectContainer(title2=title)

# The HTML.ElementFromURL create a tree structure of all the elements, attributes and data in your html documents called a DOM Tree. 
# This tree structure is necessary to pull data with xpath commands
  html = HTML.ElementFromURL(url)

# We start a for loop for all the items we want to pull off of the page.  You will need to search the source document and play around with
# and xpath checker to find the right structure to get you to a point of returning the full list of items you want to pull the data from.
  for video in html.xpath('//div/div/div/ul/li/ul/li'):
  # need to check if urls need additions and if image needs any additions to address
    url = video.xpath('./div/a//@href')[0]
    # here we are adding the sites domain name with a global variable we set at the start of the channel
    url = WebsiteURL + url
    thumb = video.xpath('./div/a/img//@style')[0]
    # A value that is returned may have extra code around it that needs to be removed. Here we use the replace string method to fix the thumb address
    thumb = thumb.replace("background-image:url('", '').replace("');", '')
    title = video.xpath('./div/div/p/a//text()')[0]

# SEE THE LINKS AT THE TOP FOR MORE DETAILED INFO ON XPATH 
# We are using xpath to get of all the values for each element with the parent element returned by the variable video 
# the syntax is: video.xpath (Ô./CHILDELEMENTÕ)[FIRSTVALUE].FORMAT or video.xpath (Ô./CHILDELEMENT/FORMATÕ)[FIRSTVALUE]
# where CHILDELEMENT is the xpath commands that gets us to the location of the data in the child element ( ex. title, url, date),
# FIRSTVALUE is the first occurrence of the child element. Usually you want to get all occurences of the child element for 
# each parent element so we give this a value of [0] (Python starts the count at zero), and FORMAT defines whether we want 
# to return the data contained in the element as text or as an attribute.  The syntax is are .text or .get(ÔATTRIBUTEÕ) 
# or //text() and //@ATTRIBUTE when attached to the child element xpath where ATTRIBUTE is the name of the attribute 
# you want to return ex. //@href or .get(href) to return the anchor attribute href="www.domainname.com/file.htm"

# this is where the values for each child element we specified are added to the channel as video clip objects the naming scheme for
# the values passed here are listed in the Framework Documentation for attributes of VideoClipObjects

    oc.add(VideoClipObject(
      url = url, 
      title = title, 
      thumb = Resource.ContentsOfURLWithFallback(thumb, fallback=R(ICON))))
      
# This code below is helpful to show when a source is empty
  if len(oc) < 1:
    Log ('still no value for objects')
    return ObjectContainer(header="Empty", message="Unable to display videos for this show right now.")      

# it will loop through and return the values for all items in the page 
  return oc



#######################################################################################################################
@route(PREFIX + '/showjson')
def ShowJSON(title):

# This function shows you how to pull data from a json data file.  First you need to determine if a json file is available for 
# the page you are trying to access.  The best way is to open the show with Chrome and use the Developers Tools.  From there you
# can see all the files that are being opened by the page you are accessing.  (Sometimes you have to hit refresh button for those
# sources to show up). I usually list them by type so the applications are listed first. It takes a little time and research to
# figure out what you are looking at and when you find a json file.  You may also have to play with the parameters like ids and
# number of results to get the list you want.

# Then you have to figure out how to ensure that you are going to use the proper url address for the json file everytime

# Below is a basic example of a json data pull

  oc = ObjectContainer(title2 = title)
  # Here we call the function we created below to find an id
  show_id = JSONID(url)
  # Below is a code I found within the hulu website to pull JSON data for their shows. So I broke the data up to add the correct show id
  # you could also make global variables for the beginning and end of the JSON address and use those to create the full JSON URl
  json_url = 'http://www.hulu.com/mozart/v1.h2o/shows/' + show_id +'/episodes?free_only=0&show_id=' + show_id + '&sort=seasons_and_release&video_type=episode&items_per_page=32&access_token=Jk0-QLbtXxtSMOV4TUnwSXqhhDM%3DaoY_yiNlac0ed1d501bee91624b25159a0c57b05d5f34fa3dc981da5c5e9169daf661ffb043b2805717849b7bdeb8e01baccc43f'

  # This is the API used to parse data from JSON
  videos = JSON.ObjectFromURL(json_url)
  # Enter a for loop to run through all data sets of the type data
  for video in videos['data']:
  # Below this is the format for pulling data from the JSON data from the structure of the Hulu JSON file which requires 
  # going a little deeper into the structure of the file to pull the data.  Often you will see JSON parses that just go in one level
  # Ex. url = video['url']. You may have to play with the code to find the right combination for your JSON data
    url = video['video']['id']
    # this particular site does not provide a proper url link, so we are using a variable to make the id work
    url = WebsiteEpURL + str(url)
    title = video['video']['title']
    thumb = video['video']['thumbnail_url']
    duration = video['video']['duration']
    # the duration must be in milliseconds so at the least you will need to usually multiply it by 1000
    # duration = int(duration) * 1000
    # The code below will change it from a MM:SS format to milliseconds 
    # duration = Datetime.MillisecondsFromString(duration)
    date = video['video']['available_at']
    date = Datetime.ParseDate(date)
    summary = video['video']['description']

    oc.add(EpisodeObject(
      url = url, 
      title = title,
      thumb = Resource.ContentsOfURLWithFallback(thumb, fallback=R(ICON)),
      summary = summary,
      # (this code is not accurate for Hulu and just added to show as an example)
      # duration = duration,
      originally_available_at = date))

  if len(oc) < 1:
    Log ('still no value for objects')
    return ObjectContainer(header="Empty", message="Unable to display videos for this show right now.")      

  return oc

###############################################################################################################
# This function pulls the ID from each show page for it to be entered into the JSON data url
# The example below pulls the id from one of two places in the source of the web page 
# it first looks for a list id and then looks for a content id based on global regex variables set at the top
# of this program
@route(PREFIX + '/jsonid')
def JSONID(url):

  ID = ''
  content = HTTP.Request(url).content
  try:
    ID = RE_LIST_ID.search(content).group(1)
  except:
    ID = RE_CONTENT_ID.search(content).group(1)
  return ID

#############################################################################################################################
# This is a function to pull the thumb from a the head of a page
@route(PREFIX + '/getthumb')
def GetThumb(url):
  page = HTML.ElementFromURL(url)
  try:
    thumb = page.xpath("//head//meta[@property='og:image']//@content")[0]
    if not thumb.startswith('http://'):
      thumb = http + thumb
  except:
    thumb = R(ICON)
  return thumb

###############################################################################################################
# OTHER THINGS TO LOOK AT WHEN DESIGNING YOUR CHANNEL
###############################################################################################################
#
# DEBUG LOG MESSAGES
# ANYWHERE IN YOUR CODE THAT YOU WANT TO PUT A DEBUG CODE THAT RETURNS A LINE OF TEXT OR A VARIABLE
# YOU WOULD USE THE LOG COMMAND.  THE PROPER FORMAT IS BELOW:
# To just include a statement, add Log('I am here') To return the value of a variable VAR in the log statement, 
# you would add Log('the value of VAR is %s' %VAR)
#
# PYTHON STRING METHODS
# CHECK OUT THE PYTHON STRING METHODS. THESE GIVE YOU SEVERAL WAYS TO MANIPULATE STRINGS THAT CAN BE HELPFUL IN YOUR CHANNEL CODE
# THIS IS A GOOD PAGE WITH BASIC TUTORIALS AND EXPLANATIONS FOR STRING METHODS: 'http://www.tutorialspoint.com/python/python_strings.htm'
#
# XML XPATH CHECKER
# TRADITIONAL XPATH CHECKERS DO NOT WORK ON XML PAGES. HERE IS A LINK TO AN XML XPATH CHECKING PROGRAM THAT IS VERY HELPFUL
# 'http://chris.photobooks.com/xml/default.htm'
# 
# TRY/EXCEPT 
# TRY IS GOOD FOR SITUATIONS WHERE YOUR XPATH COMMANDS MAY OR MAY NOT WORK. IF YOUR XPATH IS OUT OF RANGE YOU WILL GET ERRORS IN YOUR
# CODE.  USING TRY ALLOWS YOU TO TRY THE XPATH AND IF IT DOESN'T WORK, PUT ALTERNATIVE CODE UNDER EXCEPT AND YOU WILL NOT GET ERRORS
# IN YOUR CODE
#
# DICT[] 
# DICT[] IS PART OF THE PLEX FRAMEWORK THAT ALLOWS YOU TO SAVE DATA IN A GLOBAL VARIABLE THAT IS RETAINED WHEN YOU EXIT THE PLUGIN
# SO YOU CAN PULL IT UP IN MULTIPLE FUNCTIONS WITHOUT PASSING THE VARIABLES FROM FUNCTION TO FUNCTION. AND IT CAN BE ACCESSED AND USED
# OVER MULTIPLE SESSIONS