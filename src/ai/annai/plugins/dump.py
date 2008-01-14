"""Test plugin handler.

A lot of checks take place in this module (all if __debug__: things)
which are not really necessary; they are only put in here to make the
plugin useful for checking any code that uses the plugins.

"""
import httplib
import re

from ai.annai.plugins import BasePlugin
import communication as c
import frontends

# Create a lock for fetching.
_fetch_mutex = c.Timed_Mutex(3)

class _Plugin(BasePlugin):
    #: Regular expression used to search for dump requests.
    rex = re.compile(r"\bdump\b\W+\#?(\d+)\b")
    def __init__(self, ident):
        pass

    def __unicode__(self):
        return u"dump plugin."

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
            reply = "Dump #%s:\n\n%s" % (dump_num, response.read().strip())
        h.close()
        return (message, reply)

class OneOnOnePlugin(_Plugin):
    """ Dump plugin for OneOnOne conversations."""
    pass

class ManyOnManyPlugin(_Plugin):
    """Dump plugin for many-on-many conversations."""
    def process(self, message, reply, sender):
        return _Plugin.process(self, message, reply) 
