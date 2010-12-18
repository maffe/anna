"""This plugin sends "k" after two other people did."""

from ai.annai.plugins import BasePlugin

class _Plugin(BasePlugin):
    def __init__(self, identity, args):
        self._kcount = 0

    def __unicode__(self):
        return u"k plugin"

    def process(self, message, reply, *args):
        if message == "k":
            self._kcount += 1
            if self._kcount == 2:
                return (u"k", u"k")
        else:
            self._kcount = 0
        return (message, reply)

OneOnOnePlugin = _Plugin
ManyOnManyPlugin = _Plugin
