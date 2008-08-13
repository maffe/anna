"""Connection handling of the IRC frontend.

Every different server that the bot must connect to has a seperate
_MyClient instance. All L{Individual}s and {Group}s use this client to
communicate with respective entities on said server.

"""
try:
    import threading as _threading
except ImportError:
    import dummy_threading as _threading
import time

import ircbot
import irclib
irclib.DEBUG = 1

import aihandler
import communication as c
import config
from frontends import BaseConnection, NoSuchParticipantError

from parties import Individual, Group, GroupMember

# Temporarily stored values here. Should be configurable, obviously.
ENC = "utf-8"
SERVER = "irc.bergnetworks.com"
PORT = 6667
CHANNEL = "#test"

_conf = config.get_conf_copy()
_def_ai_mom = aihandler.get_manyonmany(_conf.misc["default_ai"])
_def_ai_ooo = aihandler.get_oneonone(_conf.misc["default_ai"])

def _irc_nameq(x, y):
    """Returns True if two names are considered equal according to the RFC."""
    # Better to call this with unicode objects, of course, but if it is sure
    # that the encoding is ASCII compatible (IRC nicknames MUST contain only
    # ACII chars) you can call it with byte strings too.
    assert(isinstance(x, basestring))
    assert(isinstance(y, basestring))
    assert(type(x) == type(y))
    return irclib.irc_lower(x) == irclib.irc_lower(y)

class _ServerBot(ircbot.SingleServerIRCBot):
    def __init__(self, *args, **kwargs):
        ircbot.SingleServerIRCBot.__init__(self, *args, **kwargs)
        self.individuals = ircbot.IRCDict()
        self.connection.add_global_handler("join", self.late_on_join, 20)

    def late_on_join(self, conn, ev):
        """Just like an on_join handler but with higher priority number.

        This handler must be called after C{ircbot.SingleServerIRCBot}'s
        built-in on_join handler.

        """
        if _irc_nameq(irclib.nm_to_n(ev.source()), conn.get_nickname()):
            # This event was triggered because this bot just joined.
            chan_name_enc = ev.target()
            chan_name = chan_name_enc.decode(ENC)
            group = Group(conn, name=chan_name, encoding=ENC)
            group.set_AI(_def_ai_mom(group))
            self.channels[chan_name_enc]._annagroup = group

    def on_namreply(self, conn, ev):
        names = map(lambda x: (x, x.decode(ENC)), ev.arguments()[2].split())
        for name_enc, name in names:
            if _irc_nameq(name_enc, conn.get_nickname()):
               continue 
            group = self.channels[ev.arguments()[1]]._annagroup
            # Hack: the API doesn't describe a way to check if a participant is
            # already in a room, so the exception means it is not.
            try:
                group.get_participant(name)
            except NoSuchParticipantError:
                group.add_participant(GroupMember(name,
                        self.connection.get_server_name().decode(ENC)))

    def on_nick(self, conn, ev):
        from_enc = irclib.nm_to_n(ev.source())
        from_ = from_enc.decode(ENC)
        to_enc = ev.target()
        to = to_enc.decode(ENC)
        if _irc_nameq(to_enc, conn.get_nickname()):
            # Ignore incoming NICKs indicating nickchange of the bot itself.
            return
        for group in (chan._annagroup for chan in self.channels):
            try:
                gmem = group.get_participant(from_)
                gmem.nick = to
            except NoSuchParticipantError:
                pass

    def on_nicknameinuse(self, conn, ev):
        conn.nick(conn.get_nickname() + "_")

    def on_privmsg(self, conn, ev):
        msg = ev.arguments()[0].decode(ENC, "replace")
        sender_name_enc = irclib.nm_to_n(ev.source())
        sender_name = sender_name_enc.decoder(ENC)
        c.stderr(u"DEBUG: irc: PRIVMSG from %s: %s\n" % (sender, msg))
        if sender not in self.individuals:
            sender = Individual(conn, name=sender_name, encoding=ENC)
            sender.set_AI(_def_ai_ooo(sender))
            self.individuals[sender_name_enc] = sender
        self.individuals[sender_name_enc].get_AI().handle(msg)

    def on_pubmsg(self, conn, ev):
        msg = ev.arguments()[0].decode(ENC, "replace")
        sender_name = irclib.nm_to_n(ev.source().decode(ENC))
        chan_name_enc = ev.target()
        chan_name = ev.target().decode(ENC)
        c.stderr(u"DEBUG: irc: PRIVMSG (pub) from %s: %s\n" % (sender_name,
            msg))
        group = self.channels[chan_name_enc]._annagroup
        try:
            part = group.get_participant(sender_name)
        except NoSuchParticipantError, e:
            part = GroupMember(sender_name,
                    self.connection.get_server_name().decode(ENC))
            group.add_participant(part)
        group.get_AI().handle(msg, part)

    def on_welcome(self, conn, ev):
        try:
            c.stderr(u"INFO: irc: %s\n" % ev.arguments()[0].decode(ENC))
        except UnicodeDecodeError:
            c.stderr(u"WARNING: irc: Failed to parse the welcome message from"
                    " %s.\n" % SERVER)
        conn.join(CHANNEL)

class Connection(BaseConnection, _threading.Thread):
    def __init__(self):
        _threading.Thread.__init__(self, name="IRC frontend")

    def connect(self):
        # The connection will be closed when this is set to True.
        self.halt = False
        self.start()

    def disconnect(self):
        self.halt = True

    def run(self):
        nick = _conf.misc["bot_nickname"].encode(ENC)
        bot = _ServerBot([(SERVER, PORT)], nick, nick)
        bot._connect()
        c.stderr(u"DEBUG: irc: Connected.\n")
        while not self.halt:
            bot.ircobj.process_once(1)
        bot.disconnect()
        c.stderr(u"DEBUG: irc: finished.\n")
