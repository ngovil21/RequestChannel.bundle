PREFIX = "/video/plexrequestchannel"

KEYS = list('abcdefghijklmnopqrstuvwxyz1234567890-=;[]\\\',./')
SHIFT_KEYS = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()_+:{}|\"<>?')


def Start():
    if 'DumbKeyboard-History' not in Dict:
        Dict['DumbKeyboard-History'] = []
        Dict.Save()


@route(PREFIX + "/dumbkeyboard/keyboard")
def Keyboard(caller, query=None, shift=False, secure=False, **kwargs):
    if secure and query is not None:
        string = ''.join(['*' for i in range(len(query[:-1]))]) + query[-1]
    else:
        string = query if query else ""

    oc = ObjectContainer()
    # Submit
    oc.add(DirectoryObject(key=Callback(Submit, caller=caller, query=query, **kwargs), title=u'%s: %s' % ('Submit', string.replace(' ', '_'))))
    # Search History
    if Dict['DumbKeyboard-History']:
        oc.add(DirectoryObject(key=Callback(History, caller=caller, secure=secure, kwargs=kwargs), title=u'%s' % 'Search History'))
    # Space
    oc.add(DirectoryObject(key=Callback(self.Keyboard, caller=caller, query=query + " " if query else " ", secure=secure, **kwargs), title='Space'))
    # Backspace (not really needed since you can just hit back)
    if query is not None:
        oc.add(DirectoryObject(key=Callback(Keyboard, caller=caller, query=query[:-1], secure=secure, **kwargs), title='Backspace'))
    # Shift
    oc.add(DirectoryObject(key=Callback(Keyboard, caller=caller, query=query, shift=(not shift), secure=secure, **kwargs), title='Shift'))
    # Keys
    for key in self.KEYS if not shift else self.SHIFT_KEYS:
        oc.add(
            DirectoryObject(key=Callback(Keyboard, caller=caller, query=query + key if query else key, secure=secure, **kwargs), title=u'%s' % key))
    return oc


@route(PREFIX + "/dumbkeyboard/history")
def History(caller, secure=False, **kwargs):
    oc = ObjectContainer()
    if Dict['DumbKeyboard-History']:
        oc.add(DirectoryObject(key=Callback(ClearHistory, caller=caller, secure=secure, **kwargs),
                               title=u'%s' % 'Clear History'))
    for item in Dict['DumbKeyboard-History']:
        oc.add(DirectoryObject(key=Callback(Keyboard, caller=caller, query=item, secure=secure, **kwargs),
                               title=u'%s' % item))
    return oc


@indirect
@route(PREFIX + "/dumbkeyboard/clearhistory")
def ClearHistory(caller, secure=False, **kwargs):
    Dict['DumbKeyboard-History'] = []
    Dict.Save()
    return History(caller, secure=secure, **kwargs)


@indirect
@route(PREFIX + "/dumbkeyboard/addhistory")
def AddHistory(query):
    if query not in Dict['DumbKeyboard-History']:
        Dict['DumbKeyboard-History'].append(query)
        Dict.Save()


@indirect
@route(PREFIX + "/dumbkeyboard/submit")
def Submit(caller, query, **callback_args):
    AddHistory(query)
    kwargs = {'query': query}
    kwargs.update(callback_args)
    return caller(**kwargs)
