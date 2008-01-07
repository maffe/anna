"""The conversation classes for the echo AI module."""

import ai
import aihandler
import frontends

class OneOnOne(ai.BaseOneOnOne):
    def __init__(self, identity):
        if not isinstance(identity, frontends.BaseIndividual):
            raise TypeError, "You can only use a OneOnOne AI for Individuals."
        self.ident = identity

    def handle(self, message):
        if message.startswith("load module "):
            ai_str = message[12:]
            try:
                ai_class = aihandler.get_oneonone(ai_str)
                new_ai = ai_class(self.ident)
                self.ident.set_AI(new_ai)
                self.ident.send("Success.")
                return
            except ValueError, e:
                self.ident.send("Failed to load module %s: %s" % (ai_str, e))
                return
        self.ident.send(message)

class ManyOnMany(ai.BaseManyOnMany):
    def __init__(self, room):
        if not isinstance(room, frontends.BaseGroup):
            raise TypeError, "You can only use a ManyOnMany AI for Groups."
        self.room = room

    def handle(self, message, sender):
        if sender.nick.lower() == self.room.get_mynick().lower():
            print >> sys.stderr, "WARNING: interpreting messages from myself."
        if message.startswith("load module "):
            ai_str = message[12:]
            try:
                ai_class = aihandler.get_manyonmany(ai_str)
                new_ai = ai_class(self.room)
                self.room.set_AI(new_ai)
                return
            except ValueError, e:
                self.room.send("Failed to load module %s: %s" % (ai_str, e))
                return
        elif message in ("!leave", "leave", "!stop", "stop", "!quit", "quit"):
            self.room.leave()
            return
        self.room.send(message)