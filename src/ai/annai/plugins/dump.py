"""Test plugin handler.

A lot of checks take place in this module (all if __debug__: things)
which are not really necessary; they are only put in here to make the
plugin useful for checking any code that uses the plugins.

"""
from ai.annai.plugins import BasePlugin
import frontends
import re
import urllib
import communication as c

# Create a lock for fetching.
_fetch_mutex = c.Timed_Mutex(10)

class _Plugin(BasePlugin):

    def process(self, message, reply):
	p = re.compile(".*dump\D*(\d+).*")
	res = p.match(message)

	if res is None:
            return (message, reply)
    	
        if not _fetch_mutex.testandset():
            return (message, u"%s overloaded, please try again later." % self)
        # The lock has been acquired. It will be released after a timeout.
    
        u = urllib.urlopen("http://b4.xs4all.nl/dump/%s?type=text"
            % res.group(1))
	result = u.read()
	if result == "This dump does not exist.\n":
            return(message, reply)
        else:
	    return (message, result)


class OneOnOnePlugin(_Plugin):
    """ Dump plugin

    @param identity: The identity associated with this plugin.
    @type identity: L{frontends.BaseIndividual}

    """
    def __init__(self, identity):
	    pass

    def __unicode__(self):
        return u"dump plugin."

    def process(self, message, reply):
        """Returns the dump with the given numer
        """
        return(_Plugin.process(self, message, reply))

class ManyOnManyPlugin(BasePlugin):
    """Dump plugin for many-on-many conversations.

    @param room: The room the discussion is taking place in.
    @type room: L{frontends.BaseGroup}

    """
    def __init__(self, room):
	    pass

    def __unicode__(self):
        return u"dump plugin."

    def process(self, message, reply, sender):
        return(_Plugin.process(self, message, reply))
