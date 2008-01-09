"""Test plugin handler.

A lot of checks take place in this module (all if __debug__: things)
which are not really necessary; they are only put in here to make the
plugin useful for checking any code that uses the plugins.

"""
from ai.annai.plugins import BasePlugin
import frontends

class OneOnOnePlugin(BasePlugin):
    """Plugin for test purposes.

    @param identity: The identity associated with this plugin.
    @type identity: L{frontends.BaseIndividual}

    """
    def __init__(self, identity):
        if __debug__:
            if not isinstance(identity, frontends.BaseIndividual):
                raise TypeError, "Identity must be an Individual instance."

    def __unicode__(self):
        return u"test plugin."

    def process(self, message, reply):
        """Do simple processing on the message (only useful for tests).

        Returns "Test plugin: success." if there was no supplied message.  If
        the current computed reply is not None a distinct message is
        appended to it.

        """
        if __debug__:
            if not (isinstance(message, unicode) or message is None) or \
                    not (isinstance(reply, unicode) or reply is None):
                raise TypeError, "Messages must be unicode objects or None."
        if reply is None:
            return (message, u"Test plugin: success.")
        else:
            return (message, u"%s - test plugin loaded" % reply)

class ManyOnManyPlugin(BasePlugin):
    """Test plugin for many-on-many conversations.

    @param room: The room the discussion is taking place in.
    @type room: L{frontends.BaseGroup}

    """
    def __init__(self, room):
        if __debug__:
            if not isinstance(room, frontends.BaseGroup):
                raise TypeError, "Room must be a Group frontend instance."

    def __unicode__(self):
        return u"test plugin."

    def process(self, message, reply, sender):
        if __debug__:
            if not (isinstance(message, unicode) or message is None) or \
                    not (isinstance(reply, unicode) or reply is None):
                raise TypeError, "Messages must be unicode objects or None."
            if not isinstance(sender, frontends.BaseGroupMember):
                raise TypeError, "Sender must be a GroupMember."
        if reply is None:
                return (message, u"Test plugin: success.")
        else:
                return (message, u"%s - test plugin loaded" % reply)
    process.__doc__ = OneOnOnePlugin.process.__doc__
