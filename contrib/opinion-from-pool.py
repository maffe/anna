"""This plugin looks for known words like "yes" or "no" and sends anna's own (random) opinion."""

from ai.annai.plugins import BasePlugin
from random import choice
import re

class _Plugin(BasePlugin):
    words = ((u"yes", u"no"),
        (u"right", u"wrong"),
        (u"true", u"false"),
        #(u"k"), # emulate the famous "k" plugin
        (u"ja", u"nein"), # German
        )
    regex_strip = re.compile(u"^(.*?)[.!?]*$", re.DOTALL)
    
    def __init__(self, identity, args):
        self.sent = False
        self.oldpool = ()

    def __unicode__(self):
        return u"opinion plugin"

    def process(self, message, reply, *args):
        if message is None:
            return (None, reply)
        stripped = self.regex_strip.match(message).group(1).lower()
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
