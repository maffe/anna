"""A frontend for interaction with the bot through stdin/stdout."""

import sys

import aihandler
import communication as c
import config
from frontends import BaseIndividual

class Individual(BaseIndividual):
    def __init__(self, name=u"you"):
        self.party = name

    def __str__(self):
        return self.party

    def get_name(self):
        return self.party

    def get_type(self):
        return u"console"

    def set_name(self, name):
        if __debug__:
            if not isinstance(name, unicode):
                raise TypeError, "Name must be a unicode object."
        self.party = name

    def send(self, message):
        if __debug__:
            if not isinstance(message, unicode):
                raise TypeError, "Message must be a unicode object."
        my_name = config.get_conf_copy().misc['bot_nickname']
        if message.startswith("/me "):
            c.stdout_block(u"*%s %s\n" % (my_name, message[4:]))
        else:
            c.stdout_block(u"<%s> %s\n" % (my_name, message))
