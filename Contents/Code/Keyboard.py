KEYS = 'abcdefghijklmnopqrstuvwxyz1234567890-=;[]\\\',./'
SHIFT_KEYS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()_+:{}|\"<>?'

TITLE = 'Plex Request Channel'
PREFIX = '/video/plexrequestchannel'


@route(PREFIX + "/dumbtools/keyboard")
def Keyboard(query=None, callback=None, shift=False, secure='False', locked='locked'):
    if 'DumbKeyboard-History' not in Dict:
        Dict['DumbKeyboard-History'] = []

    Log.Debug("Keyboard created.")
    if secure == 'True' and query is not None:
        string = ''.join(['*' for i in range(len(query[:-1]))]) + query[-1]
    else:
        string = query if query else ""

    oc = ObjectContainer()
    # Submit
    Log.Debug("Create Submit key")
    oc.add(DirectoryObject(key=Callback(callback, query=query, locked=locked), title=u'%s: %s' % ('Submit', string.replace(' ', '_'))))
    # Search History
    if Dict['DumbKeyboard-History']:
        Log.Debug("Create History")
        oc.add(DirectoryObject(key=Callback(History, callback=callback, locked=locked), title=u'%s' % 'Search History'))
    # Space
    Log.Debug("Create Space Key")
    oc.add(DirectoryObject(key=Callback(Keyboard, query=query + " " if query else " ", callback=callback, locked=locked, secure=secure),
                           title='Space'))
    # Backspace (not really needed since you can just hit back)
    if query is not None:
        Log.Debug("Create backspace key")
        oc.add(DirectoryObject(key=Callback(Keyboard, query=query[:-1], callback=callback, locked=locked, secure=secure), title='Backspace'))
    # Shift
    Log.Debug("Create Shift Key")
    oc.add(DirectoryObject(key=Callback(Keyboard, query=query, callback=callback, locked=locked, secure=secure, shift=True), title='Shift'))
    # Keys
    Log.Debug("Generating keys")
    for key in KEYS if not shift else SHIFT_KEYS:
        oc.add(DirectoryObject(key=Callback(Keyboard, query=query + key if query else key, callback=callback, locked=locked, secure=secure),
                               title=u'%s' % key))
    Log.Debug("Return Object Container")
    return oc


@route(PREFIX + "/dumbtools/history")
def History(callback=None, locked='locked'):
    oc = ObjectContainer()
    if Dict['DumbKeyboard-History']:
        oc.add(DirectoryObject(key=Callback(ClearHistory, callback=callback, locked=locked),
                               title=u'%s' % 'Clear History'))
    for item in Dict['DumbKeyboard-History']:
        oc.add(DirectoryObject(key=Callback(self.Submit, query=item),
                               title=u'%s' % item))
    return oc


@route(PREFIX + "/dumbtools/clearhistory")
def ClearHistory(callback=callback, locked=locked):
    Dict['DumbKeyboard-History'] = []
    Dict.Save()
    return History(callback=callback, locked=locked)


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
