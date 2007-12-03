"""Frontends are used to interact with the bot.

More information on frontends (including the API) can be found on the wiki:
<http://0brg.net/anna/wiki/Frontends>

"""
__all__ = ["xmpp", "console"]

class BaseIndividual(object):
    """Parent-class for classes that represent individuals in dialogues."""
    pass

class BaseGroup(object):
    """Parent-class for classes representing a group having a conversation."""
    pass

class BaseGroupMember(BaseIndividual):
    """Parent-class for classes representing a member of a Group chat."""
    pass

class BaseConnection(object):
    """Connection with the medium in question."""
    pass
