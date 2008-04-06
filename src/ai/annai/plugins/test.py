"""Test plugin handler.

A lot of checks take place in this module (all if __debug__: things)
which are not really necessary; they are only put in here to make the
plugin useful for checking any code that uses the plugins.

"""
from ai.annai.plugins import BasePlugin, PluginError
import frontends

class _Plugin(BasePlugin):
    """Base class for the test plugin."""
    def __unicode__(self):
        return u"test plugin."

    def unloaded(self):
        self.party.send(u"Test plugin unloaded.")

class OneOnOnePlugin(_Plugin):
    """Plugin for test purposes.

    @param identity: The identity associated with this plugin.
    @type identity: L{frontends.BaseIndividual}

    """
    def __init__(self, identity, args):
        if __debug__:
            if not isinstance(identity, frontends.BaseIndividual):
                raise TypeError, "Identity must be an Individual instance."
        self.party = identity

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
        if message == "crashtest":
            raise PluginError, u"Test plugin crashing itself..."
        elif reply is None:
            return (message, u"Test plugin: success.")
        else:
            return (message, u"%s - test plugin loaded" % reply)

class ManyOnManyPlugin(_Plugin):
    """Test plugin for many-on-many conversations.

    @param room: The room the discussion is taking place in.
    @type room: L{frontends.BaseGroup}

    """
    def __init__(self, room, args):
        if __debug__:
            if not isinstance(room, frontends.BaseGroup):
                raise TypeError, "Room must be a Group frontend instance."
        self.party = room

    def __unicode__(self):
        return u"test plugin."

    def process(self, message, reply, sender, highlight):
        if __debug__:
            if not (isinstance(message, unicode) or message is None) or \
                    not (isinstance(reply, unicode) or reply is None):
                raise TypeError, "Messages must be unicode objects or None."
            if not isinstance(sender, frontends.BaseGroupMember):
                raise TypeError, "Sender must be a GroupMember."
            assert(highlight is True or highlight is False)
        if message == "crashtest":
            raise PluginError, u"Test plugin crashing itself..."
        elif message == "highlight":
            return (message, unicode(highlight))
        elif reply is None:
            return (message, u"Test plugin: success.")
        else:
            return (message, u"%s - test plugin loaded" % reply)
    process.__doc__ = OneOnOnePlugin.process.__doc__
