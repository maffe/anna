"""Plugin for U{http://b4.xs4all.nl/dump/}."""

import httplib
import re

from ai.annai.plugins import BasePlugin
import communication as c
import frontends

# Create a lock for fetching.
_fetch_mutex = c.TimedMutex(3)

class _Plugin(BasePlugin):
    #: Regular expression used to search for dump requests.
    # There is no word-boundary (\b) after "dump" to allow dump123.
    rex = re.compile(r"\bdump\W*?\#?(\d+)\b", re.IGNORECASE)
    def __init__(self, ident, args):
        pass

    def __unicode__(self):
        return u"dump plugin"

    def process(self, message, reply):
	res = self.rex.search(message)
	if res is None:
            return (message, reply)
        dump_num = res.group(1)
        if not _fetch_mutex.testandset():
            return (message, u"%s overloaded, please try again later." % self)
        # The lock has been acquired. It will be released after a timeout.

        h = httplib.HTTPConnection("b4.xs4all.nl")
        h.request("GET", "/dump/%s?type=text" % dump_num)
        response = h.getresponse()
        if response.status == 200:
            encoding = response.getheader("content-type").split("charset=")[1]
            dump_content = response.read().decode(encoding, "replace").strip()
            reply = "Dump #%s:\n\n%s" % (dump_num, dump_content)
        h.close()
        return (message, reply)

class OneOnOnePlugin(_Plugin):
    """ Dump plugin for OneOnOne conversations."""
    pass

class ManyOnManyPlugin(_Plugin):
    """Dump plugin for many-on-many conversations."""
    def process(self, message, reply, sender):
        return _Plugin.process(self, message, reply) 
