"""Conversation-party definitions for the xmpp frontend."""

import sys
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

import communication as c
from frontends import BaseIndividual, BaseGroup, BaseGroupMember

class Individual(BaseIndividual):
    def __init__(self, jid, stream):
        c.stderr(u"DEBUG: xmpp: Individual %s instantiated.\n" % jid)
        self.jid = jid
        self.name = jid.node
        self.stream = stream

    def __str__(self):
        return "xmpp:%s" % self.jid

    def __unicode__(self):
        return u"xmpp:%s" % unicode(self.jid)

    def get_AI(self):
        return self.ai

    def get_name(self):
        return self.name

    def get_type(self):
        return "xmpp"

    def set_AI(self, ai):
        self.ai = ai

    def set_name(self, name):
        self.name = name

    def send(self, message):
        if __debug__:
            if not isinstance(message, unicode):
                raise TypeError, "Message must be a unicode object."
        message = px.Message(to_jid=self.jid, body=message,
                stanza_type="chat")
        self.stream.send(message)

class Group(BaseGroup):
    """The mucstate variable is a px.jab.muc.MucRoomState instance.

    It must be set before it can be used.

    """
    mucstate = None
    def __init__(self, jid, stream):
        c.stderr(u"DEBUG: xmpp: Group %s instantiated.\n" % jid)
        assert(isinstance(jid, px.JID))
        self.jid = jid
        self.members = []

    def __str__(self):
        return "xmpp:%s" % self.jid

    def __unicode__(self):
        return u"xmpp:%s" % unicode(self.jid)

    def add_participant(self, participant):
        if not isinstance(participant, GroupMember):
            raise TypeError, "Participants must be GroupMember instances."
        self.members.append(participant)

    def del_participant(self, participant):
        if __debug__:
            if not isinstance(participant, GroupMember):
                raise TypeError, "Participants must be GroupMember instances."
        try:
            self.members.remove(participant)
        except ValueError:
            raise NoSuchParticipantError, participant.nick

    def get_AI(self):
        return self.ai

    def get_mynick(self):
        return self.mucstate.get_nick()

    def get_participant(self, name):
        assert(isinstance(name, unicode))
        for part in self.members:
            if name == part.nick:
                return part
        raise NoSuchParticipantError, name

    def get_participants(self):
        """Get an iterable with all the participants."""
        return tuple(self.members)

    def get_type(self):
        return "xmpp"

    def is_active(self):
        return self.mucstate.joined

    def join(self):
        if __debug__:
            c.stderr(u"DEBUG: join %s\n" % self)
        self.mucstate.join(history_maxstanzas=0)

    def leave(self):
        if __debug__:
            c.stderr(u"DEBUG: leaving %s\n" % self)
        self.mucstate.leave()

    def set_AI(self, ai):
        self.ai = ai

    def set_mynick(self, nick):
        try:
            self.mucstate.change_nick(nick)
        except px.pyxmpp.xmppstringprep.StringprepError, e:
            self.send(u"Error changing nick: %s" % e)

    def send(self, message):
        if __debug__:
            if not isinstance(message, unicode):
                raise TypeError, "Message must be a unicode object."
        self.mucstate.send_message(message)

class GroupMember(px.jab.muc.MucRoomUser, BaseGroupMember):
    def __init__(self, room, *args):
        """Store a reference to the Group instance and create MucRoomUser().

        The arguments besides the second one (room) are passed to
        pyxmpp.jabber.muc.MucRoomUser.__init__().

        """
        px.jab.muc.MucRoomUser.__init__(self, *args)
        self.room = room

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

class NoSuchParticipantError(Exception):
    """Raised when an unknown GroupMember is adressed."""
    def __init__(self, name):
        Exception.__init__(self, name)
        self.name = name
    def __repr__(self):
        return "Participant %s does not exist." % self.name
    __str__ = __repr__
