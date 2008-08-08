"""This plugin looks for known words like "yes" or "no" and sends anna's own (random) opinion."""

from ai.annai.plugins import BasePlugin
from random import choice
import re

class _Plugin(BasePlugin):
    sent = False
    oldpool = ()
    words = ((u"yes", u"no"),
        (u"right", u"wrong"),
        #(u"k"), # emulate the famous "k" plugin
        (u"ja", u"nein"), # German
        )
    regex_strip = re.compile(u"^(.*?)[.!?]*$")

    def __unicode__(self):
        return u"opinion plugin"

    def process(self, message, reply, *args):
        stripped = self.regex_strip.match(message).group(1)
        for pool in self.words:
            if stripped in pool:
                if pool == self.oldpool:
                    if not self.sent:
                        self.sent = True
                        return (message, choice(pool))
                    return (message, reply)
                else:
                    self.oldpool = pool
                    self.sent = False
                    return (message, reply)
        # message not found in any pool
        self.oldpool = ()
        self.sent = False
        return (message, reply)

OneOnOnePlugin = _Plugin
ManyOnManyPlugin = _Plugin
