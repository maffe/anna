"""Web search plugin for the annai AI module.

Provides several functions for searching the web about a given keyword.
Currently only implements searching the english wikipedia.

"""
import httplib
import re
import urllib

from ai.annai.plugins import BasePlugin
import frontends 

# ATTENTION PROGRAMMERS: remember that these plugins, too, are threaded! Do not
# write to global variables!

# Use a dictionary with keys 'lang' and 'q' to format this to a proper get
# request for google webservers.
_wiki_get = "/search?hl=%(lang)s&sitesearch=%(lang)s.wikipedia.org&q=%(q)s"
_default_messages = dict(en=dict(
        WNOTFOUND=u"whaddayamean?",
        WFOUND=u"i found your article! take a look at it..",
        WGOOGLEFOUND=u"i searched google.com for that.. is it this?",
        ))
_find_wiki_rex = "(?<=href=\")http://%s.wikipedia.org/wiki/\S*(?=\")"

class _Plugin(BasePlugin):
    def __init__(self, peer):
        self.lang = u"en"
        # Use the global dictionary (no writing occurs so its thread-safe).
        self.messages = _default_messages
        # The different search types.
        self._mods = dict(
                w=self.wikipedia,
                )

    def __unicode__(self):
        return u"web search plugin"

    def process(self, message, reply):
        msg = message.strip()
        # Using None as delimiter makes split() use its default values.
        try:
            cmd, arg = msg.split(None, 1)
            return (message, self._mods[cmd](arg))
        except (ValueError, KeyError):
            # Assume the message was not intended for this plugin if either:
            # ValueError: There were no spaces in the message.
            # KeyError: the first word of the message is not a registered
            # search type.
            return (message, reply)

    def wikipedia(self, tofind):
        """Searches Wikipedia and returns the URI to the matching article.

        Returns the location of the article.

        """
        # If wikipedia has found the article, the HTTP reply contains 
        # a Location: header.
        tofind = urllib.pathname2url(tofind)
        con = httplib.HTTPConnection("%s.wikipedia.org" % self.lang, 80)
        con.connect()
        con.request("GET", "/wiki/Special:Search?search=%s&go=Go" % tofind)
        location = con.getresponse().getheader("location", 1)
        con.close()

        if location != 1:
            return u"%s\n%s" % (self.messages[self.lang]["WFOUND"], location)
        # else search google: "wikipedia %s" % tofind
        con = httplib.HTTPConnection("www.google.com", 80)
        con.connect()
        con.request("GET", _wiki_get % dict(lang=self.lang, q=tofind))
        response = con.getresponse().read()
        con.close()

        regex = re.search(_find_wiki_rex % self.lang, response)
        if regex != None:
            return u"%s\n%s" % (self.messages[self.lang]["WGOOGLEFOUND"],
                    regex.group(0))
        # if you haven't found anything there too return a sad message,
        return self.messages[self.lang]["WNOTFOUND"]

class OneOnOnePlugin(_Plugin):
    pass

class ManyOnManyPlugin(_Plugin):
    def process(self, message, reply, sender):
        reply = OneOnOnePlugin.process(self, message, reply)[1]
        return (message, u"%s: %s" % (sender.nick, reply))
