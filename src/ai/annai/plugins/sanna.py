"""Web search plugin for the annai AI module.

Provides several functions for searching the web about a given keyword.
Currently only implements searching the english wikipedia.

"""
import httplib
import logging
import re
import urllib

from ai.annai.plugins import BasePlugin
import communication as c
import frontends 

# ATTENTION PROGRAMMERS: remember that these plugins, too, are threaded! Do not
# write to global variables!

# Use a dictionary with keys 'lang' and 'q' to format this to a proper get
# request for google webservers.
#_WIKI_GET = "/search?hl=%(lang)s&sitesearch=%(lang)s.wikipedia.org&q=%(q)s"

# NEW! Use a dictionary with keys 'lang' and 'q' to format this to a proper get
# request for dogpile webservers.
_WIKI_GET = "".join(("/dogpile/ws/results/Web/%(q)s/1/485/TopNavigation/",
                    "Relevance/iq=true/zoom=off/_iceUrlFlag=7?_IceUrl=true",
                    "&adv=qall%%3d%(q)s%%26domaini%%3dinclude%%26domaint",
                    "%%3d%(lang)s.wikipedia.org"))

_DEFAULT_MESSAGES = dict(
        WNOTFOUND=u"whaddayamean?",
        WFOUND=u"i found your article! take a look at it..",
        WWEBFOUND=u"i searched the web for that.. is it this?",
        )
_FIND_WIKI_REX = "(?<=window\.status=\')http://%s.wikipedia.org/wiki/\S*(?=\';)"
_DEFAULT_HTTP_HEADERS = {"user-agent": 
        "Mozilla/5.0 (compatible; Anna/1; +http://0brg.net/anna/)"}

# Create a lock for fetching.
_fetch_mutex = c.TimedMutex(5)
_logger = logging.getLogger("anna." + __name__)

class _Plugin(BasePlugin):
    def __init__(self, peer, args):
        self.lang = u"en"
        # Use the global dictionary (no writing occurs so its thread-safe).
        self.messages = _DEFAULT_MESSAGES
        # The different search types.
        self._mods = {
                u"w": self.wikipedia,
                }

    def __unicode__(self):
        return u"web search plugin"

    def process(self, message, reply, *args, **kwargs):
        if message.startswith("sanna lang="):
            self.lang=message[len("sanna lang="):]
            return (message, u"k")
        msg = message.strip()
        try:
            # Using None as delimiter makes split() use its default values.
            cmd, arg = msg.split(None, 1)
        except (AttributeError, ValueError):
            # Assume the message was not intended for this plugin if either:
            # AttributeError: There is no incoming message.
            # ValueError: There were no spaces in the message.
            return (message, reply)
        if cmd in self._mods:
            func = self._mods[cmd]
        else:
            # The first word of the message is not a registered search type.
            return (message, reply)
        if not _fetch_mutex.testandset():
            return (message, u"%s overloaded, please try again later." % self)
        # The lock has been acquired. It will be released after a timeout.

        _logger.debug(u"%s(%r)", self, cmd)
        return (message, func(arg))

    def wikipedia(self, tofind):
        """Searches Wikipedia and returns the URI to the matching article.

        Returns the location of the article.

        """
        # If wikipedia has found the article, the HTTP reply contains 
        # a Location: header.
        # Encoded querystring values are first encoded to utf-8.
        assert(isinstance(tofind, unicode))
        tofind = urllib.quote_plus(tofind.encode("utf-8"))
        con = httplib.HTTPConnection("%s.wikipedia.org" % self.lang, 80)
        con.connect()
        con.request("GET", "/wiki/Special:Search?search=%s&go=Go" % tofind,
                headers=_DEFAULT_HTTP_HEADERS)
        location = con.getresponse().getheader("location", 1)
        con.close()

        if location != 1:
            return u"%s\n%s" % (self.messages["WFOUND"], location)
        # else search dogpile: "wikipedia %s" % tofind
        con = httplib.HTTPConnection("www.dogpile.com", 80)
        con.connect()
        con.request("GET", _WIKI_GET % dict(lang=self.lang, q=tofind))
        response = con.getresponse().read()
        con.close()

        regex = re.search(_FIND_WIKI_REX % self.lang, response)
        if regex is not None:
            return u"%s\n%s" % (self.messages["WWEBFOUND"],
                    regex.group(0))
        # if you haven't found anything there too return a sad message,
        return self.messages["WNOTFOUND"]

OneOnOnePlugin = _Plugin
ManyOnManyPlugin = _Plugin
