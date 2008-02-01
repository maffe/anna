"""The conversation classes for the echo AI module."""

import ai
import aihandler
import communication as c
import frontends

class OneOnOne(ai.BaseOneOnOne):
    def __init__(self, identity):
        if __debug__:
            if not isinstance(identity, frontends.BaseIndividual):
                raise TypeError, "First argument must be Individual instance."
        self.ident = identity

    def handle(self, message):
        if message.startswith("load module "):
            ai_str = message[len("load module "):]
            try:
                ai_cls = aihandler.get_oneonone(ai_str)
            except aihandler.NoSuchAIError, e:
                self.ident.send(unicode(e))
            else:
                self.ident.set_AI(ai_cls(self.ident))
                self.ident.send(u"Success.")
            return
        self.ident.send(message)

class ManyOnMany(ai.BaseManyOnMany):
    def __init__(self, room):
        if __debug__:
            if not isinstance(room, frontends.BaseGroup):
                raise TypeError, "You can only use a ManyOnMany AI for Groups."
        self.room = room

    def handle(self, message, sender):
        if sender.nick.lower() == self.room.get_mynick().lower():
            c.stderr("WARNING: interpreting messages from myself.\n")
            return
        if message.startswith("load module "):
            ai_str = message[len("load module "):]
            try:
                ai_cls = aihandler.get_manyonmany(ai_str)
            except aihandler.NoSuchAIError, e:
                self.room.send(unicode(e))
            else:
                self.room.set_AI(ai_cls(self.room))
                self.room.send(u"Success.")
            return
        elif message in ("!leave", "leave", "!stop", "stop", "!quit", "quit"):
            self.room.leave()
            return
        self.room.send(message)