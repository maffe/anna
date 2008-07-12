class BaseIndividual(object):
    """Parent-class for classes that represent individuals in dialogues."""
    pass

class BaseGroup(object):
    """Parent-class for classes representing a group having a conversation."""
    pass

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

class BaseConnection(object):
    """Connection with the medium in question."""
    pass
