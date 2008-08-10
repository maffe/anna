"""The time plugin tells you what time it is.

Use "timestr is x" to change the output formatting. The default timestr
is '%c %Z'. More information can be found on this plugin's wiki page:
U{https://0brg.net/anna/wiki/Time_plugin}.

"""
import time

from ai.annai.plugins import BasePlugin

#: Either one of these messages (with or without questionmark) triggers.
HOOKS = (
        "what time is it",
        "how late is it",
        "what's the time",
        "time",
        )

class _Plugin(BasePlugin):
    def __init__(self, identity, args):
        self._frmt = "%c %Z"

    def __unicode__(self):
        return u"time plugin"

    def process(self, message, reply, *args):
        if message is None:
            return (message, reply)
        if message.lower().rstrip(" ?") in HOOKS:
            return (message, unicode(time.strftime(self._frmt)))
        elif message.startswith("timestr is "):
            # Will probably be fixed in py3k, no need for fallback now.
            self._frmt = message[11:].encode("us-ascii", "replace")
            return (message, u"k")
        else: 
            return (message, reply)

OneOnOnePlugin = _Plugin
ManyOnManyPlugin = _Plugin
