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
FETCH_ERROR = u"An error occurred while fetching a fragment from \
irrepressible.info. If the error persists, please tell us about it on \
the wiki <http://0brg.net/anna/wiki/Annawiki_talk:Community_Portal>."

# Create a lock for fetching.
_fetch_mutex = c.TimedMutex(10)

def get_ii_fragment(**filters):
    """Fetch a (random) fragment, optionally using given filter.

    Assumes the remote server encodes content in utf-8. For more information on
    the available filters, see U{http://irrepressible.info/api}.

    @return: Information about the fragment: (id, content, url).
    @rtype: C{tuple} of C{unicode} objects
    @raise IOError: An error occurred opening the URL.
    @raise xml.parsers.expat.ExpatError: The XML is not well-formed.
    @TODO: Catch C{AttributeError} when xml is well-formed but not like we
        expect it to be anymore.

    """
    filters["limit"] = 1
    filters["random"] = True
    params = urllib.urlencode(filters)
    u = urllib.urlopen(_URL_BASE % params)
    doc = xml.dom.minidom.parse(u)
    u.close()
    # These operations can raise an AttributeError (because one of the
    # attributes is actually None instead of an XML node) if the XML format is
    # suddenly changed.
    fragment = doc.firstChild.firstChild.nextSibling.firstChild.nextSibling
    id = fragment.getAttribute("id")
    url = fragment.getAttribute("href")
    content = fragment.getElementsByTagName("fragmentText")[0].firstChild.data
    return (id, content, url)

class _Plugin(BasePlugin):
    def __init__(self, peer, args):
        self.peer = peer

    def __unicode__(self):
        return u"irrepressible.info plugin"

    def process(self, message, reply):
        if not message == "ii":
            return (message, reply)
        elif not _fetch_mutex.testandset():
            return (message, u"%s overloaded, please try again later." % self)
        # The lock has been acquired. It will be released after a timeout.

        if __debug__:
            c.stderr(u"NOTICE: %s: fetching fragment.\n" % self)
        try:
            frag = get_ii_fragment()
        except (IOError, xml.parsers.expat.ExpatError), e:
            c.stderr(e)
            return (message, FETCH_ERROR)
        else:
            return (message, u"Fragment %s:\n\t%s\nfrom: <%s>" % frag)

class OneOnOnePlugin(_Plugin):
    pass

class ManyOnManyPlugin(_Plugin):
    def process(self, message, reply, sender):
        return _Plugin.process(self, message, reply)
