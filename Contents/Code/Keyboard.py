#Modified version of DumbTools for Plex v1.1 by Cory <babylonstudio@gmail.com>

KEYS = list('abcdefghijklmnopqrstuvwxyz1234567890-=;[]\\\',./')
SHIFT_KEYS = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()_+:{}|\"<>?')

TITLE = 'Plex Request Channel'
PREFIX = '/video/plexrequestchannel'


@route(PREFIX + "/dumbtools/keyboard")
def Keyboard(query=None, callback=None, parent=None, shift=False, secure='False', locked='locked', title="Search", message=None):
    if 'DumbKeyboard-History' not in Dict:
        Dict['DumbKeyboard-History'] = []

    Log.Debug("Keyboard created.")
    if secure == 'True' and query is not None:
        string = ''.join(['*' for i in range(len(query[:-1]))]) + query[-1]
    else:
        string = query if query else ""

    oc = ObjectContainer(title2=title, header=TITLE, message=message)
    # Submit
    Log.Debug("Create Submit key")
    oc.add(DirectoryObject(key=Callback(callback, query=query, locked=locked), title=u'%s: %s' % ('Submit', string.replace(' ', '_'))))
    # Search History
    if Dict['DumbKeyboard-History']:
        Log.Debug("Create History")
        oc.add(DirectoryObject(key=Callback(History, query=query, callback=callback, locked=locked, secure=secure), title=u'%s' % 'Search History'))
    # Space
    Log.Debug("Create Space Key")
    oc.add(DirectoryObject(key=Callback(Keyboard, query=query + " " if query else " ", callback=callback,parent=parent, locked=locked, secure=secure, title=title),
                           title='Space'))
    # Backspace (not really needed since you can just hit back)
    if query is not None:
        Log.Debug("Create backspace key")
        oc.add(DirectoryObject(key=Callback(Keyboard, query=query[:-1], callback=callback, parent=parent, locked=locked, secure=secure, title=title), title='Backspace'))
    # Shift
    Log.Debug("Create Shift Key")
    oc.add(
        DirectoryObject(key=Callback(Keyboard, query=query, callback=callback, parent=parent, locked=locked, secure=secure, shift=True, title=title), title='Shift'))
    # Keys
    Log.Debug("Generating keys")
    if parent:
        oc.add(DirectoryObject(key=Callback(parent, locked=locked), title="Cancel"))
    for key in KEYS if not shift else SHIFT_KEYS:
        oc.add(
            DirectoryObject(key=Callback(Keyboard, query=query + key if query else key, callback=callback, parent=parent, locked=locked, secure=secure, title=title),
                            title=u'%s' % key))
    Log.Debug("Return Object Container")
    return oc


@route(PREFIX + "/dumbtools/history")
def History(query=None, callback=None, parent=None, locked='locked', secure='False'):
    oc = ObjectContainer()
    oc.add(DirectoryObject(key=Callback(Keyboard, query=query, callback=callback, parent=parent, locked=locked, secure=secure), title="Return to Keyboard"))
    if Dict['DumbKeyboard-History']:
        oc.add(DirectoryObject(key=Callback(ClearHistory, callback=callback, parent=parent, locked=locked, secure=secure),
                               title=u'%s' % 'Clear History'))
    for item in Dict['DumbKeyboard-History']:
        oc.add(DirectoryObject(key=Callback(callback, query=item, locked=locked),
                               title=u'%s' % item))
    return oc


@route(PREFIX + "/dumbtools/clearhistory")
def ClearHistory(query="", callback=None, parent=None, locked='locked', secure='False'):
    Dict['DumbKeyboard-History'] = []
    Dict.Save()
    return Keyboard(query=query, callback=callback, parent=parent, locked=locked, secure=secure)


@route(PREFIX + "/dumbtools/addhistory")
def AddHistory(query):
    if query not in Dict['DumbKeyboard-History']:
        Dict['DumbKeyboard-History'].append(query)
        Dict.Save()

# @route(PREFIX + "/dumbtools/submit")
# def Submit(query, callback=callback, locked=locked):
#     self.AddHistory(query)
#     kwargs = {'query': query}
#     kwargs.update(self.callback_args)
#     return Callback(**kwargs)
