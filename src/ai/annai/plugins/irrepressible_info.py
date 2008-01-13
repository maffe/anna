"""Plugin for U{http://irrepressible.info/}.

Fetches quotes on-demand an at random intervals (customizable). Only
allows one fetch every ten seconds.

"""
try:
    import threading as _threading
except ImportError:
    import dummy_threading as _threading
import urllib
import xml.dom.minidom
import xml.parsers.expat

from ai.annai.plugins import BasePlugin
import communication as c
import frontends

_URL_BASE = "http://irrepressible.info/query?%s"

# Create a lock for fetching.
_fetch_mutex = c.Timed_Mutex(10)

def get_ii_fragment(**filters):
    """Fetch a (random) fragment, optionally using given filter.

    Assumes the remote server encodes content in utf-8. For more information on
    the available filters, see U{http://irrepressible.info/api}.

    @return: Information about the fragment: (id, content, url).
    @rtype: C{tuple} of C{unicode} objects
    @raise IOError: An error occurred opening the URL.
    @raise xml.parsers.expat.ExpatError: The XML is not well-formed.

    """
    filters["limit"] = 1
    filters["random"] = True
    params = urllib.urlencode(filters)
    u = urllib.urlopen(_URL_BASE % params)
    doc = xml.dom.minidom.parse(u)
    u.close()
    fragment = doc.firstChild.firstChild.nextSibling.firstChild.nextSibling
    id = fragment.getAttribute("id")
    url = fragment.getAttribute("href")
    content = fragment.getElementsByTagName("fragmentText")[0].firstChild.data
    return (id, content, url)

class _Plugin(BasePlugin):
    def __init__(self, peer):
        self.peer = peer

    def __unicode__(self):
        return u"irrepressible.info plugin."

    def process(self, message, reply):
        if not message == "ii":
            return (message, reply)
        elif not _fetch_mutex.testandset():
            return (message, u"%s overloaded, please try again later." % self)
        # The lock has been acquired. It will be released after a timeout.

        if __debug__:
            c.stderr(u"NOTICE: %s: fetching fragment.\n" % self)
        return (message, u"Fragment %s:\n\t%s\nfrom: <%s>" % get_ii_fragment())

class OneOnOnePlugin(_Plugin):
    pass

class ManyOnManyPlugin(_Plugin):
    def process(self, message, reply, sender):
        return _Plugin.process(self, message, reply)
