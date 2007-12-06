"""A frontend for interaction with the bot through stdin/stdout."""

import sys

import aihandler
import config
from frontends import BaseIndividual

class Individual(BaseIndividual):
    def __init__(self, name="you"):
        self.party = name

    def __str__(self):
        return self.party

    def get_AI(self):
        return aihandler.getAIReferenceByUID(0)

    def get_name(self):
        return self.party

    def get_type(self):
        return "console"

    def set_AI(self, ai):
        return aihandler.setAID(0, ai.ID)

    def set_name(self, name):
        self.party = name

    def send(self, message):
        my_name = config.misc['bot_nickname']
        if message.startswith("/me "):
            print "*", my_name, message[4:].encode(sys.stdout.encoding)
        else:
            print "<%s>" % my_name, message.encode(sys.stdout.encoding)