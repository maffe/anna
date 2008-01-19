"""Plugin that fetches and interprets news feeds."""

from ai.annai.plugins import BasePlugin, PluginError
import frontends

# A local import ('import _feedparser') would make more sense but for some
# reason that does not work.
from ai.annai.plugins import _feedparser

class _Plugin(BasePlugin):
    def __init__(self, party, args):
        if len(args) != 1:
            raise PluginError, u"Usage: load plugin feedparser <feed-url>"
        self.feed_url = args[0]

    def __unicode__(self):
        return u"feed parser plugin for <%s>." % self.feed_url

    def process(self, message, reply, sender=None):
        return (message, reply)

class OneOnOnePlugin(_Plugin):
    pass

class ManyOnManyPlugin(_Plugin):
    pass
