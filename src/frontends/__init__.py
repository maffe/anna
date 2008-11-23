"""Frontends are used to interact with the bot.

More information on frontends (including the API) can be found on the
U{wiki <https://0brg.net/anna/wiki/Frontends>}.

"""
__all__ = ["xmpp", "console", "irc"]

class NoSuchParticipantError(Exception):
    """Raised when an unknown GroupMember is adressed."""
    def __init__(self, name):
        Exception.__init__(self, name)
        self.name = name
    def __repr__(self):
        return "Participant %s does not exist." % self.name
    __str__ = __repr__

class BaseConnection(object):
    """Connection with the medium in question."""
    def connect(self):
        pass
    def disconnect(self):
        pass
    def join(self):
        pass

class BaseIndividual(object):
    """Parent-class for classes that represent individuals in dialogues."""
    def destroy(self):
        self.get_AI().destroy()
    def get_AI(self):
        return self.ai
    def get_name(self):
        return u""
    def get_type(self):
        return u""
    def set_AI(self, AI_module):
        self.ai = AI_module
    def set_name(self, name):
        if not isinstance(name, unicode):
            raise TypeError, "Name must be a unicode object."
    def send(self, message):
        if not isinstance(message, unicode):
            raise TypeError, "Message must be a unicode object."

class BaseGroup(object):
    """Parent-class for classes representing a group having a conversation."""
    def destroy(self):
        self.leave()
        for p in self.get_participants():
            self.del_participant(p)
        self.get_AI().destroy()
    def join(self):
        pass
    def leave(self):
        pass
    def send(self, message):
        if not isinstance(message, unicode):
            raise TypeError, "Message must be a unicode object."
    def get_AI(self):
        return self.ai
    def get_type(self):
        return u""
    def get_mynick(self):
        return u""
    def is_joined(self):
        return False
    def set_AI(self, AI_module):
        self.ai = AI_module
    def set_mynick(self, nick):
        if not isinstance(nick, unicode):
            raise TypeError, "Nickname must be a unicode object."
    def add_participant(self, part):
        if not isinstance(part, BaseGroupMember):
            raise TypeError, "Participant must be a GroupMember instance."
    def del_participant(self, part):
        if not isinstance(part, BaseGroupMember):
            raise TypeError, "Participant must be a GroupMember instance."
        raise NoSuchParticipantError, part.nick
    def get_participant(self, nick):
        if not isinstance(nick, unicode):
            raise TypeError, "Nickname must be a unicode object."
        raise NoSuchParticipantError, nick
    def get_participants(self):
        return ()

class BaseGroupMember(object):
    """Parent-class for classes representing a member of a Group chat.
    
    This base class allows for creation of custom-named group member instances
    conforming to the API.
    
    """
    def __init__(self, nick):
        assert(isinstance(nick, unicode))
        self.nick = nick
    def __str__(self):
        return self.nick.encode("us-ascii", "replace")
    def __unicode__(self):
        return self.nick
