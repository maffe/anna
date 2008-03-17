"""The time plugin tells you what time it is.

Use "timestr is x" to change the output formatting.

"""
import time

from ai.annai.plugins import BasePlugin, PluginError
import frontends

#: Either one of these messages (with or without questionmark) triggers.
HOOKS = (
        "what time is it",
        "how late is it",
        "what's the time",
        "time",
        )

class _Plugin(BasePlugin):
    def __init__(self, identity, args):
        self._frmt = "%c"

    def __unicode__(self):
        return u"time plugin"

    def process(self, message, reply, *args):
        if message.lower().rstrip(" ?") in HOOKS:
            return (message, unicode(time.strftime(self._frmt)))
        elif message.startswith("timestr is "):
            self._frmt = message[11:]
            return (message, u"k")
        else: 
            return (message, reply)

OneOnOnePlugin = _Plugin
ManyOnManyPlugin = _Plugin
