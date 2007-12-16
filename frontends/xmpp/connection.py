"""Connect to the xmpp network and define connection handlers."""

import getpass
import sys

import pyxmpp.all as px
import pyxmpp.jabber.all as pxj
import pyxmpp.jabber.muc as pxjm
px.jab = pxj
px.jab.muc = pxjm
del pxj, pxjm

import aihandler
import config
from frontends.xmpp import parties
from frontends import BaseConnection

class Connection(px.jab.Client, BaseConnection):
    """A talk-specific connection with the other party.

    Controls the comm ng handlers for incoming messages.

    """
    UNSUPPORTED_TYPE = u"Sorry, this type of messages is not supported."""
    CHOOSE_AI = u"Please choose an AI from the list first:\n%s"

    def __init__(self, jid=None, password=None):
        self.conf = config.get_conf_copy()
        # Everybody waiting to be assigned an AI instance.
        self._aichoosers = []
        # List of party instances known to the bot. Maps JIDs to Identities.
        self._parties = {}
        jid, password = self.get_creds()
        px.jab.Client.__init__(self, jid, password)

    def _create_AI_list(self):
        """Creates a textual representation of the available AIs."""
        def_ai = self.conf.misc["default_ai"]
        ais = []
        for name in aihandler.get_names():
            if name.lower() == def_ai.lower():
                ais.append("%s (default)" % name)
            else:
                ais.append(name)
        return self.CHOOSE_AI % u"\n".join(["- %s" % ai for ai in ais])

    def _send(self, *args, **kwargs):
        """Do not use this function, use the Individual/Group's send instead.

        This is intended for INTERNAL use by this specific class (things like
        debug messages and default replies), NOT for use in actually sending a
        message crafted by some AI to a peer.

        """
        message = px.Message(*args, **kwargs)
        self.stream.send(message)
        if __debug__:
            marsh = message.serialize().decode("utf-8") # unicode object.
            marsh = marsh.encode(sys.stdout.encoding, "replace") # byte string.
            print >> sys.stderr, "DEBUG: sending '%s'" % marsh

    def choose_AI(self, party, message, is_room):
        """Handles conversations with this party when no AI is assigned yet.

        The first argument is an pyxmpp.JID instance of the party starting a
        new conversation, the second one is the message they sent. The is_room
        argument specifies whether this is a groupchat or PM.

        If this is a PM and there is no cached Individual instance available
        for this party a new instance is created and stored. Rooms are always
        expected to be instantiated and cached in the self._parties dictionary.

        """
        assert(isinstance(party, px.JID))
        text = unicode(message.get_body()).strip()
        # If this party already got the "choose AI" message this message he
        # sent must be his choice. Parse it as such.
        if party in self._aichoosers:
            if text == "":
                choice = def_ai
            elif text.endswith(" (default)"):
                # If the user thought " (default)" was part of the name, strip.
                choice = text[:-len(" (default)")]
            else:
                choice = text
            try:
                if is_room:
                    ai_class = aihandler.get_manyonmany(text)
                else:
                    ai_class = aihandler.get_oneonone(text)
            except aihandler.NoSuchAIError, e:
                msg = u"\n\n".join((unicode(e), self._create_AI_list()))
            else:
                if is_room:
                    # Rooms are already instantiated somewhere else.
                    idnty = self._parties[party]
                else:
                    idnty = parties.Individual(party, self.stream)
                    self._parties[party] = idnty
                idnty.set_AI(ai_class(idnty))
                self._aichoosers.remove(party)
                assert(party not in self._aichoosers)
                msg = "Great success!"
        else:
            msg = self._create_AI_list()
            self._aichoosers.append(party)
        self._send(to_jid=party, body=msg, stanza_type=message.get_type())

    def connect(self):
        """Go into an endless loop polling for new messages."""
        # Problem is that PyXMPP's API also describes the connect() method,
        # which should not be overwritten in our case. So we have to call it
        # explicitly to initiate this instance.
        px.jab.Client.connect(self)
        print "XMPP frontend started."
        self.loop()

    def exit(self):
        """Disconnect and exit.""" 
        if self.stream:
            self.lock.acquire()
            self.stream.disconnect()
            self.stream.close()
            self.stream = None
            self.lock.release()
            time.sleep(1)
        if __debug__:
            print >> sys.stderr, "DEBUG: xmpp.Connection.exit called"

    def get_creds(self):
        """Get the JID and password from the config or user."""
        jab_conf = self.conf.jabber
        args = (jab_conf["user"], jab_conf["server"], jab_conf["resource"])
        jid = px.JID(*args)
        passw = self.conf.jabber["password"]
        if not passw:
            try:
                msg = u"Please enter the password for %s: " % unicode(jid)
                passw = getpass.getpass(msg.encode(sys.stdout.encoding,
                                                                "replace"))
                passw = passw.decode(sys.stdin.encoding)
            except EOFError:
                passw = u""
                print
            except KeyboardInterrupt:
                passw = u""
                print
        if not passw:
            print >> sys.stderr, "WARNING: empty password."
        return jid, passw

    def handle_msg_chat(self, message):
        text = message.get_body()
        sender = px.JID(message.get_from())
        try:
            ai = self._parties[sender].get_AI()
            ai.handle(text)
        except KeyError:
            self.choose_AI(sender, message, is_room=False)
        if __debug__:
            msg = u"DEBUG: chat: '%s' from '%s'" % (text, sender)
            print >> sys.stderr, msg.encode(sys.stdout.encoding, "replace")
        return True

    def handle_msg_unsup(self, message):
        # TODO: send error stanza.
        if message.get_type() == "normal":
            return self.handle_mucinvite(message)
        self._send(to_jid=message.get_from(), body=self.UNSUPPORTED_TYPE,
                stanza_type=message.get_type())
        if __debug__:
            msg = u"DEBUG: unhandled: %s" % message.serialize().decode("utf-8")
            print >> sys.stderr, msg.encode(sys.stdout.encoding, "replace")
        return True

    def handle_mucinvite(self, message):
        if __debug__:
            msg = u"DEBUG: xmpp: invited to %s" % message.get_from()
            print >> sys.stderr, msg.encode(sys.stdout.encoding, "replace")
        ns_map = {"mu": "http://jabber.org/protocol/muc#user"}
        nick = self.conf.misc["bot_nickname"]
        ai_list = self._create_AI_list()
        if not message.xpath_eval("/ns:message/mu:x/mu:invite", ns_map):
            # This stanza is not an invitation to a MUC.
            return False
        try:
            room_jid = px.JID(message.get_from().bare())
        except px.JIDError, e:
            msg = u"WARNING: handle_mucinvite: %s" % unicode(e)
            print >> sys.stderr, msg.encode(sys.stdout.encoding, "replace")
            return True
        if room_jid in self._parties:
            msg = u"WARNING: already in %s" % unicode(room_jid)
            print >> sys.stderr, msg.encode(sys.stdout.encoding, "replace")
            return True
        # Room without AI until a module is assigned.
        room = parties.Group(room_jid, self.stream)
        handler = _MucEventHandler(self, room)
        self.rooms.join(room_jid, nick, handler, history_maxstanzas=0)
        room.mucstate = self.rooms.rooms[unicode(room_jid)]
        # Send an AI choice prompt manually.
        self._parties[room_jid] = room
        self._aichoosers.append(room_jid)
        self._send(to_jid=room_jid, body=ai_list, stanza_type="groupchat")
        return True

    def session_started(self):
        """Called by pyxmpp when the session has succesfully started."""
        # Priorities in PyXMPP are from low to high.
        self.stream.set_message_handler(typ="chat", priority=30,
                handler=self.handle_msg_chat)
        self.stream.set_message_handler(typ=None, priority=50,
                handler=self.handle_mucinvite)
        self.stream.set_message_handler(typ="normal", priority=70,
                handler=self.handle_msg_unsup)
        #self.stream.set_iq_get_handler("query", "jabber:iq:version",
        #                            handler=self.handle_version)
        self.rooms = px.jab.muc.MucRoomManager(self.stream)
        self.rooms.set_handlers(priority=40)

    def state_change(*args):
        """Debug handler overwriting parent method."""
        print >> sys.stderr, "DEBUG: state_change(%s, %s, %s)" % args

class _MucEventHandler(px.jab.muc.MucRoomHandler):
    """Define handlers for events from MUC rooms.

    This includes everything from topic changes to incoming messages. Note that
    this class implements some hacks that make it virtually unsusable anywhere
    outside this module. Doing so is discouraged.

    """
    def __init__(self, connection, room):
        """Store some information about the room this handler belongs to.

        The room argument must be a parties.Group instance.

        """
        if not isinstance(room, parties.Group):
            raise TypeError, "Wrong type room: %s" % type(room)
        px.jab.muc.MucRoomHandler.__init__(self)
        self.conn = connection
        self.room = room

    def message_received(self, sender, message):
        try:
            room_jid = px.JID(message.get_from()).bare()
        except JIDError:
            return True
        if sender is None or sender.room_jid == self.room.mucstate.room_jid:
            # Ignore messages from the conference server and this bot.
            return True
        text = message.get_body()
        if __debug__:
            msg = u"DEBUG: groupchat: %s: '%s'" % (message.get_from(), text)
            print >> sys.stderr, msg.encode(sys.stdout.encoding, "replace")
        # Rooms always have an instance stored in the _parties dictionary.
        room = self.conn._parties[room_jid]
        if room_jid in self.conn._aichoosers:
            self.conn.choose_AI(room_jid, message, is_room=True)
        else:
            ai = room.get_AI()
            member = room.get_participant(sender.nick)
            ai.handle(text, member)
        return True

    def user_joined(self, user, stanza):
        self.room.add_participant(parties.GroupMember(self.room, user))
        if __debug__:
            msg = u"DEBUG: %s entered %s." % (user.nick, unicode(self.room))
            print >> sys.stderr, msg.encode(sys.stdout.encoding)
        return True
