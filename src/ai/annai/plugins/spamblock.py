"""This plugin allows for a little control over how much the bot talks.

This is useful to prevent spamming in crowded rooms and loops with other
bots.  To make full use of its protection, load this plugin as the last
plugin in the list.

"""
import time

from ai.annai.plugins import BasePlugin

class _Plugin(BasePlugin):
    def __init__(self, party, args):
        # The time of the last outgoing message to the minute exact.
        self.lastmsg = time.gmtime()[:5]
        # Maximum amount of outgoing message per minute.
        self.limit = 20
        # Number of messages sent since the start of minute self.lastmsg.
        self.msgnum = 0
        self.prefix = u"!spam"

    def __unicode__(self):
        return u"spamblock plugin"

    def process(self, message, reply):
        now = time.gmtime()[:5]

        if message.startswith("%s rate " % self.prefix):
            rest = message[(len(" rate ") + len(self.prefix)):].strip()
            try:
                self.limit = int(rest)
            except ValueError:
                return (message, reply)
            return (message, self.limit == 0 and u"limit removed" or u"k.")

        # This plugin is only concerned with outgoing messages.
        if reply is None:
            return (message, reply)

        # Check the number of messages since this minute began:
        if self.lastmsg != now:
            self.msgnum = 1
            self.lastmsg = now
        else:
            self.msgnum += 1

        if 0 < self.limit < self.msgnum:
            # Stay quiet (reply = None).
            return (message, None)
        else:
            return (message, reply)

class OneOnOnePlugin(_Plugin):
    pass

class ManyOnManyPlugin(_Plugin):
    def process(self, message, reply, sender):
        return _Plugin.process(self, message, reply)
