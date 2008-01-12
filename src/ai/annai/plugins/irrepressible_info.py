"""Plugin for u{http://irrepressible.info/}.

Fetches quotes on-demand an at random intervals (customizable).

"""
import urllib
import xml.dom.minidom

from ai.annai.plugins import BasePlugin
import communication as c
import frontends

_url_base = "http://irrepressible.info/query?%s"

def get_ii_fragment(**filters):
    """Fetch a (random) fragment, optionally using given filter.

    Assumes the remote server encodes content in utf-8. For more information on
    the available filters, see U{http://irrepressible.info/api}.

    @return: The content of the specified url.
    @rtype: A C{tuple} of C{unicode} objects: (id, content, url).
    @raise IOError: An error occurred opening the URL.
    @raise xml.parsers.expat.ExpatError: The XML is not well-formed.

    """
    filters["limit"] = 1
    filters["random"] = True
    params = urllib.urlencode(filters)
    u = urllib.urlopen(_url_base % params)
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
        if __debug__:
            c.stderr("NOTICE: irrepressible.info plugin: fetching fragment.\n")
        return (message, u"Fragment %s:\n\t%s\nfrom: <%s>" % get_ii_fragment())

class OneOnOnePlugin(_Plugin):
    pass

class ManyOnManyPlugin(_Plugin):
    def process(self, message, reply, sender):
        return _Plugin.process(self, message, reply)
