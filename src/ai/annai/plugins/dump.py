"""Plugin for U{http://b4.xs4all.nl/dump/}.

See U{https://0brg.net/anna/wiki/Dump_plugin} for more information.

"""
import httplib
import re
try:
    import thread as _thread
except ImportError:
    import dummy_thread as _thread

from ai.annai.plugins import BasePlugin
import communication as c
import frontends

# Create a timeout lock for accepting requests for fetching dumps.
_fetch_mutex = c.TimedMutex(3)
# A hard mutex that will only allow one fetch at a time (in case the server
# takes longer to respond than the TimedMutex timeout).
_fetch_lock = _thread.allocate_lock()

def _get_dump(party, id):
    """Get a dump with given id and send the contents to this peer."""
    _fetch_lock.acquire()
    h = httplib.HTTPConnection("b4.xs4all.nl")
    h.request("GET", "/dump/%s?type=text" % id)
    response = h.getresponse()
    if response.status == 200:
        encoding = response.getheader("content-type").split("charset=")[1]
        content = response.read().decode(encoding, "replace").strip()
        party.send(u"Dump #%s:\n\n%s" % (id, content))
    h.close()
    _fetch_lock.release()

class _Plugin(BasePlugin):
    #: Regular expression used to search for dump requests.
    rex = re.compile(r"\bdump\W*?\#?(\d+|random)\b")
    # There is no word-boundary (\b) after "dump" to allow dump123.
    def __init__(self, party, args):
        self.party = party

    def __unicode__(self):
        return u"dump plugin"

    def process(self, message, reply, *args, **kwargs):
	res = self.rex.search(message.lower())
	if res is None:
            return (message, reply)
        dump_id = res.group(1)
        if not _fetch_mutex.testandset() or _fetch_lock.locked():
            return (message, u"%s overloaded, please try again later." % self)
        else:
            # The lock has been acquired. It will be released after a timeout.
            _thread.start_new_thread(_get_dump, (self.party, dump_id))
            return (message, reply)

class OneOnOnePlugin(_Plugin):
    """ Dump plugin for OneOnOne conversations."""
    pass

class ManyOnManyPlugin(_Plugin):
    """Dump plugin for many-on-many conversations."""
    pass
