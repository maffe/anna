"""Parent classes for AI modules."""

import frontends

class BaseOneOnOne(object):
    """Parent-class for classes representing one-on-one convos with a peer.
    
    @param individual: The other peer in this conversation.
    @type individual: L{frontends.BaseIndividual}
    
    """
    def __init__(self, individual):
        pass

    def destroy(self):
        """Clean up AI instance."""
        pass

    def handle(self, message):
        """Process incoming message.

        @param message: The incoming message.
        @type message: C{unicode}

        """
        pass

class BaseManyOnMany(object):
    """Parent-class for classes representing group conversation.

    @param room: The conversation room.
    @type room: L{frontends.BaseGroup}

    """
    def __init__(self, room):
        pass

    def destroy(self):
        """Clean up AI instance."""
        pass

    def handle(self, message, member):
        """Process incoming message.

        @param message: The incoming message.
        @type message: C{unicode}
        @param member: The group member that sent this message.
        @type member: L{frontends.BaseGroupMember}

        """
        pass
