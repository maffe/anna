"""This plugin repeats a repeated "k" (once)."""

from ai.annai.plugins import BasePlugin

class _Plugin(BasePlugin):
    def __init__(self, identity, args):
        self.sent = False
        self.wask = False

    def __unicode__(self):
        return u"repeat k plugin"

    def process(self, message, reply, *args):
        if message == u"k":
            if self.wask:
                if not self.sent:
                    self.sent = True
                    return (u"k", u"k")
            self.wask = True
        else:
            self.sent = False
            self.wask = False
        return (message, reply)

OneOnOnePlugin = _Plugin
ManyOnManyPlugin = _Plugin
