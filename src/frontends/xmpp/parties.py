"""Conversation-party definitions for the xmpp frontend."""

import logging
try:
    import threading as _threading
except ImportError:
    import dummy_threading as _threading

import pyxmpp.all as px
import pyxmpp.jabber.all as pxj
import pyxmpp.jabber.muc as pxjm
import pyxmpp.jabber.muccore as pxjmc
px.jab = pxj
px.jab.muc = pxjm
px.jab.muccore = pxjmc
del pxj, pxjm, pxjmc

from frontends import BaseIndividual, BaseGroup, BaseGroupMember
from frontends import NoSuchParticipantError

_logger = logging.getLogger("anna." + __name__)

class Individual(BaseIndividual):
    def __init__(self, jid, stream):
        _logger.debug(u"Individual %s instantiated.", jid)
        self._jid = jid
        self._name = jid.node
        self._stream = stream

    def __str__(self):
        return "xmpp:%s" % self._jid

    def __unicode__(self):
        return u"xmpp:%s" % unicode(self._jid)

    def get_AI(self):
        return self._ai

    def get_name(self):
        return self._name

    def get_type(self):
        return "xmpp"

    def set_AI(self, ai):
        self._ai = ai

    def set_name(self, name):
        self._name = name

    def send(self, message):
        if __debug__:
            if not isinstance(message, unicode):
                raise TypeError, "Message must be a unicode object."
        _logger.debug(u"pm -> %s: '%s'", self, message)
        message = px.Message(to_jid=self._jid, body=message,
                stanza_type="chat")
        self._stream.send(message)

class Group(BaseGroup):
    """XMPP MUC room binding for the Anna bot.

    @ivar _mucstate: Must be set before this instance can be used.
    @type _mucstate: C{pyxmpp.jabber.muc.MucRoomState}
    @ivar _members: All members of this group chat.
    @type _members: C{[L{GroupMember}, ...]}
    @ivar _jid: JID of this room.
    @type _jid: C{pyxmpp.jid.JID}

    """
    _mucstate = None
    def __init__(self, jid, stream):
        _logger.debug(u"Group %s instantiated.", jid)
        assert(isinstance(jid, px.JID))
        self._jid = jid
        self._members = []

    def __str__(self):
        return "xmpp:%s" % self._jid

    def __unicode__(self):
        return u"xmpp:%s" % unicode(self._jid)

    def add_participant(self, participant):
        if not isinstance(participant, GroupMember):
            raise TypeError, "Participants must be GroupMember instances."
        self._members.append(participant)

    def del_participant(self, participant):
        if __debug__:
            if not isinstance(participant, GroupMember):
                raise TypeError, "Participants must be GroupMember instances."
        try:
            self._members.remove(participant)
        except ValueError:
            raise NoSuchParticipantError, participant.nick

    def get_AI(self):
        return self._ai

    def get_mynick(self):
        return self._mucstate.get_nick()

    def get_participant(self, name):
        assert(isinstance(name, unicode))
        for part in self._members:
            if name == part.nick:
                return part
        raise NoSuchParticipantError, name

    def get_participants(self):
        """Get an iterable with all the participants."""
        return tuple(self._members)

    def get_type(self):
        return "xmpp"

    def is_joined(self):
        return self._mucstate.joined

    def join(self):
        _logger.debug(u"Join %s.", self)
        self._mucstate.join(history_maxstanzas=0)

    def leave(self):
        _logger.debug(u"Leave %s.", self)
        self._mucstate.leave()

    def set_AI(self, ai):
        self._ai = ai

    def set_mynick(self, nick):
        try:
            self._mucstate.change_nick(nick)
        except px.pyxmpp.xmppstringprep.StringprepError, e:
            self.send(u"Error changing nick: %s" % e)

    def send(self, message):
        if __debug__:
            if not isinstance(message, unicode):
                raise TypeError, "Message must be a unicode object."
        self._mucstate.send_message(message)

class GroupMember(px.jab.muc.MucRoomUser, BaseGroupMember):
    def __init__(self, room, *args):
        """Store a reference to the Group instance and create MucRoomUser().

        The arguments besides the second one (room) are passed to
        pyxmpp.jabber.muc.MucRoomUser.__init__().

        """
        px.jab.muc.MucRoomUser.__init__(self, *args)
        self._room = room

    def __eq__(self, y):
        if not isinstance(y, GroupMember):
            raise TypeError, "Can only compare two GroupMembers."
        return self.same_as(y)

    def __neq__(self, y):
        if not isinstance(y, GroupMember):
            raise TypeError, "Can only compare two GroupMembers."
        return not self.same_as(y)

    def __str__(self):
        return "xmpp:%s" % str(self.room_jid)

    def __unicode__(self):
        return u"xmpp:%s" % unicode(self.room_jid)
