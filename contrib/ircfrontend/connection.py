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

class _ServerBot(ircbot.SingleServerIRCBot):
    def __init__(self, *args, **kwargs):
        ircbot.SingleServerIRCBot.__init__(self, *args, **kwargs)
        self.individuals = ircbot.IRCDict()
        self.connection.add_global_handler("join", self.late_on_join, 20)

    def late_on_join(self, conn, ev):
        """Just like an on_join handler but with higher priority number.

        This handler must be called after C{SingleServerIRCBot}'s built-in
        on_join handler.

        """
        if irclib.nm_to_n(ev.source()) == conn.get_nickname():
            # This event was triggered because this bot just joined.
            chan_name_enc = ev.target()
            chan_name = chan_name_enc.decode(ENC)
            chan = Group(conn, name=chan_name, encoding=ENC)
            chan.set_AI(_def_ai_mom(chan))
            self.channels[chan_name_enc]._annagroup = chan

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
        chan = self.channels[chan_name_enc]._annagroup
        try:
            part = chan.get_participant(sender_name)
        except NoSuchParticipantError, e:
            part = GroupMember(nick,
                    self.connection.get_server_name().decode(ENC))
            chan.add_participant(part)
        chan.get_AI().handle(msg, part)

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
