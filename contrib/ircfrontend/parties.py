"""Communication parties for the IRC frontend."""

import sys

import irclib

import aihandler
import communication as c
import config
from frontends import BaseIndividual, BaseGroup, BaseGroupMember
from frontends import NoSuchParticipantError

import connection

class _IRCParty(object):
    def __init__(self, conn, name, encoding="us-ascii"):
        assert(isinstance(conn, irclib.ServerConnection))
        assert(isinstance(name, unicode))
        self._conn = conn
        self._name = name
        self._name_enc = name.encode(encoding)
        self._enc = encoding

    def __unicode__(self):
        return u"irc://%s/%s" % (self._conn.server.decode("us-ascii"),
            self._name)

    def get_type(self):
        return u"IRC"

    def send(self, message):
        if __debug__:
            if not isinstance(message, unicode):
                raise TypeError, "Message must be a unicode object."
        for line in message.split("\n"):
            self._conn.privmsg(self._name_enc, line.encode(self._enc))

class Individual(_IRCParty, BaseIndividual):
    def get_name(self):
        return self._name

    def set_name(self, name):
        if __debug__:
            if not isinstance(name, unicode):
                raise TypeError, "Name must be a unicode object."
        self._name = name

class Group(_IRCParty, BaseGroup):
    def __init__(self, *args, **kwargs):
        _IRCParty.__init__(self, *args, **kwargs)
        BaseGroup.__init__(self)
        self._is_joined = False
        self._parts = []

    def join(self):
        self._conn.join(self._chan_enc)
        self._is_joined = True

    def leave(self):
        self._conn.part(self._chan_enc)
        self._is_joined = False

    def get_mynick(self):
        return self._conn.get_nickname().decode(self._enc)

    def is_joined(self):
        return self._is_joined

    def set_mynick(self, nick):
        assert(isinstance(nick, unicode))
        self._conn.nick(nick.encode(self._enc))

    def add_participant(self, part):
        assert(isinstance(part, GroupMember))
        assert(part not in self._parts) # Needs GroupMember.__eq__.
        self._parts.append(part)

    def del_participant(self, part):
        assert(isinstance(part, GroupMember))
        try:
            self._members.remove(part)
        except ValueError:
            raise NoSuchParticipantError, part.nick

    def get_participant(self, nick):
        assert(isinstance(nick, unicode))
        for p in self._parts:
            if p.nick == nick:
                return p
        raise NoSuchParticipantError, nick

    def get_participants(self):
        return tuple(self._parts)

class GroupMember(BaseGroupMember):
    def __init__(self, nick, server):
        assert(isinstance(nick, unicode))
        assert(isinstance(server, unicode))
        self.nick = nick
        self._serv = server
    def __unicode__(self):
        return u"irc://%s/%s" % (self._serv, self.nick)
    def __eq__(self, x):
        return self.nick == x.nick and self._serv == x._serv
