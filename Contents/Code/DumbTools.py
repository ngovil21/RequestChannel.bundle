# DumbTools for Plex v1.1 by Cory <babylonstudio@gmail.com>
# Slightly modified by ngovil21 for Plex Request Channel

import urllib2

#NO_MESSAGE_CONTAINER_CLIENTS is now deprecated, using known clients that work with message overlays instead
NO_MESSAGE_CONTAINER_CLIENTS = ['Plex for iOS', 'tvOS', 'Plex for Apple TV', 'Plex for Xbox One', 'iOS', 'Mystery 4', 'Samsung',
                                'Plex for Samsung']
MESSAGE_OVERLAY_CLIENTS = ['Android', 'Roku', 'Konvergo', 'Plex Web']


class DumbKeyboard:
    CLIENTS = ['Plex for iOS', 'Plex Media Player', 'Plex Home Theater', 'OpenPHT', 'Plex for Roku', 'iOS', 'Roku', 'tvOS' 'Konvergo',
               'Plex for Apple TV', 'Plex for Xbox 360', 'Plex for Xbox One', 'Xbox One', 'Mystery 4', 'Plex for Vizio', 'Plex TV']

    KEYS = list('abcdefghijklmnopqrstuvwxyz1234567890-=;[]\\\',./')
    SHIFT_KEYS = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()_+:{}|\"<>?')

    def __init__(self, prefix, oc, callback, parent_call=None, dktitle=None, dkthumb=None,
                 dkplaceholder=None, dksecure=False, message=None, **kwargs):
        cb_hash = hash(str(callback) + str(kwargs))
        Log.Debug("Generated callback hash: " + str(cb_hash))
        Route.Connect(prefix + '/dumbkeyboard/%s/keyboard' % cb_hash, self.Keyboard)
        Route.Connect(prefix + '/dumbkeyboard/%s/submit' % cb_hash, self.Submit)
        Route.Connect(prefix + '/dumbkeyboard/%s/history' % cb_hash, self.History)
        Route.Connect(prefix + '/dumbkeyboard/%s/history/clear' % cb_hash, self.ClearHistory)
        Route.Connect(prefix + '/dumbkeyboard/%s/history/add/{query}' % cb_hash, self.AddHistory)
        Log.Debug("Generated Keyboard Routes")
        # Log.Debug(str(Callback(self.Keyboard)))
        # Add our directory item
        oc.add(DirectoryObject(key=Callback(self.Keyboard, query=dkplaceholder, message=message),
                               title=str(dktitle) if dktitle else u'%s' % 'DumbKeyboard Search', thumb=dkthumb))

        if 'DumbKeyboard-History' not in Dict:
            Dict['DumbKeyboard-History'] = []

        self.Callback = callback
        self.callback_args = kwargs
        self.secure = dksecure
        self.parent_call = parent_call

    def Keyboard(self, query=None, shift=False, message=None):
        # Log.Debug("Keyboard created.")
        if self.secure and query is not None:
            string = ''.join(['*' for i in range(len(query[:-1]))]) + query[-1]
        else:
            string = query if query else ""

        oc = ObjectContainer()
        if message and (Client.Product in MESSAGE_OVERLAY_CLIENTS or Client.Platform in MESSAGE_OVERLAY_CLIENTS):
            oc.message = message
        # Submit
        # Log.Debug("Create Submit key")
        oc.add(DirectoryObject(key=Callback(self.Submit, query=query),
                               title=u'%s: %s' % ('Submit', string)))
        #                      title=u'%s: %s' % ('Submit', string.replace(' ', '_')))), -why replace with underscores?
        # Search History
        if Dict['DumbKeyboard-History']:
            # Log.Debug("Create History")
            oc.add(DirectoryObject(key=Callback(self.History),
                                   title=u'%s' % 'Search History'))
        # Space
        # Log.Debug("Create Space Key")
        oc.add(DirectoryObject(key=Callback(self.Keyboard,
                                            query=query + " " if query else " "),
                               title='Space'))
        # Backspace (not really needed since you can just hit back)
        if query is not None:
            # Log.Debug("Create backspace key")
            oc.add(DirectoryObject(key=Callback(self.Keyboard, query=query[:-1]),
                                   title='Backspace'))
        # Shift
        # Log.Debug("Create Shift Key")
        oc.add(DirectoryObject(key=Callback(self.Keyboard, query=query, shift=True),
                               title='Shift'))
        # Cancel - return to parent
        if self.parent_call:
            oc.add(DirectoryObject(key=self.parent_call, title="Cancel"))
        # Keys
        # Log.Debug("Generating keys")
        for key in self.KEYS if not shift else self.SHIFT_KEYS:
            oc.add(DirectoryObject(key=Callback(self.Keyboard,
                                                query=query + key if query else key),
                                   title=u'%s' % key))
        # Log.Debug("Return Object Container")
        return oc

    def History(self):
        oc = ObjectContainer()
        if Dict['DumbKeyboard-History']:
            oc.add(DirectoryObject(key=Callback(self.ClearHistory),
                                   title=u'%s' % 'Clear History'))
        for item in Dict['DumbKeyboard-History']:
            oc.add(DirectoryObject(key=Callback(self.Submit, query=item),
                                   title=u'%s' % item))
        return oc

    def ClearHistory(self):
        Dict['DumbKeyboard-History'] = []
        Dict.Save()
        return self.History()

    def AddHistory(self, query):
        if query not in Dict['DumbKeyboard-History']:
            Dict['DumbKeyboard-History'].append(query)
            Dict.Save()

    def Submit(self, query):
        self.AddHistory(query)
        kwargs = {'query': query}
        kwargs.update(self.callback_args)
        return self.Callback(**kwargs)


class DumbPrefs:
    clients = ['Plex for iOS', 'Plex Media Player', 'Plex Home Theater',
               'OpenPHT', 'Plex for Roku']

    def __init__(self, prefix, oc, title=None, thumb=None):
        self.host = 'http://127.0.0.1:32400'
        try:
            self.CheckAuth()
        except Exception as e:
            Log.Error('DumbPrefs: this user cant access prefs: %s' % str(e))
            return

        Route.Connect(prefix + '/dumbprefs/list', self.ListPrefs)
        Route.Connect(prefix + '/dumbprefs/listenum', self.ListEnum)
        Route.Connect(prefix + '/dumbprefs/set', self.Set)
        Route.Connect(prefix + '/dumbprefs/settext', self.SetText)
        oc.add(DirectoryObject(key=Callback(self.ListPrefs),
                               title=title if title else 'Preferences',
                               thumb=thumb))
        self.prefix = prefix
        self.GetPrefs()

    def GetHeaders(self):
        headers = Request.Headers
        headers['Connection'] = 'close'
        return headers

    def CheckAuth(self):
        """ Only the main users token is accepted at /myplex/account """
        headers = {'X-Plex-Token': Request.Headers.get('X-Plex-Token', '')}
        req = urllib2.Request("%s/myplex/account" % self.host, headers=headers)
        res = urllib2.urlopen(req)

    def GetPrefs(self):
        data = HTTP.Request("%s/:/plugins/%s/prefs" % (self.host, Plugin.Identifier),
                            headers=self.GetHeaders())
        prefs = XML.ElementFromString(data).xpath('/MediaContainer/Setting')

        self.prefs = [{'id': pref.xpath("@id")[0],
                       'type': pref.xpath("@type")[0],
                       'label': pref.xpath("@label")[0],
                       'default': pref.xpath("@default")[0],
                       'secure': True if pref.xpath("@secure")[0] == "true" else False,
                       'values': pref.xpath("@values")[0].split("|") \
                           if pref.xpath("@values") else None
                       } for pref in prefs]

    def Set(self, key, value):
        HTTP.Request("%s/:/plugins/%s/prefs/set?%s=%s" % (self.host,
                                                          Plugin.Identifier,
                                                          key, value),
                     headers=self.GetHeaders(),
                     immediate=True)
        return ObjectContainer()

    def ListPrefs(self):
        oc = ObjectContainer(no_cache=True)
        for pref in self.prefs:
            do = DirectoryObject()
            value = Prefs[pref['id']] if not pref['secure'] else \
                ''.join(['*' for i in range(len(Prefs[pref['id']]))])
            title = u'%s: %s = %s' % (L(pref['label']), pref['type'], L(value))
            if pref['type'] == 'enum':
                do.key = Callback(self.ListEnum, id=pref['id'])
            elif pref['type'] == 'bool':
                do.key = Callback(self.Set, key=pref['id'],
                                  value=str(not Prefs[pref['id']]).lower())
            elif pref['type'] == 'text':
                if Client.Product in DumbKeyboard.clients:
                    DumbKeyboard(self.prefix, oc, self.SetText,
                                 id=pref['id'],
                                 dktitle=title,
                                 dkplaceholder=Prefs[pref['id']],
                                 dksecure=pref['secure'])
                else:
                    oc.add(InputDirectoryObject(key=Callback(self.SetText, id=pref['id']),
                                                title=title))
                continue
            else:
                do.key = Callback(self.ListPrefs)
            do.title = title
            oc.add(do)
        return oc

    def ListEnum(self, id):
        oc = ObjectContainer()
        for pref in self.prefs:
            if pref['id'] == id:
                for i, option in enumerate(pref['values']):
                    oc.add(DirectoryObject(key=Callback(self.Set, key=id, value=i),
                                           title=u'%s' % option))
        return oc

    def SetText(self, query, id):
        return self.Set(key=id, value=query)
