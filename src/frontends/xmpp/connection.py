"""Connect to the xmpp network and define connection handlers."""

import getpass
import sys
try:
    import threading as _threading
except ImportError:
    import dummy_threading as _threading

import pyxmpp.all as px
import pyxmpp.jabber.all as pxj
import pyxmpp.jabber.muc as pxjm
px.jab = pxj
px.jab.muc = pxjm
del pxj, pxjm

import aihandler
import communication as c
import config
from frontends.xmpp import parties
from frontends import BaseConnection

class Connection(px.jab.Client, _threading.Thread):
    """Threaded connection to an XMPP server.

    Set the halt attribute to False to halt a connected instance.

    """
    UNSUPPORTED_TYPE = u"Sorry, this type of messages is not supported."""
    CHOOSE_AI = u"Please choose an AI from the list first:\n%s"

    def __init__(self, **kwargs):
        _threading.Thread.__init__(self, name="xmpp frontend")
        self.conf = config.get_conf_copy()
        if "jid" not in kwargs:
            jab_conf = self.conf.jabber
            args = (jab_conf["user"], jab_conf["server"], jab_conf["resource"])
            kwargs["jid"] = px.JID(*args)
        if "password" not in kwargs:
            kwargs["password"] = self.get_passwd(kwargs["jid"])
        px.jab.Client.__init__(self, **kwargs)

        # Everybody waiting to be assigned an AI instance.
        self._aichoosers = []
        # List of party instances known to the bot. Maps JIDs to Identities.
        self._parties = {}
        # The connection will be closed when this is set to True.
        self.halt = False

    def _create_AI_list(self):
        """Creates a textual representation of the available AIs."""
        ais = []
        for name in aihandler.get_names():
            if name.lower() == self.conf.misc["default_ai"].lower():
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
            c.stderr(u"DEBUG: xmpp: sending '%s'\n" % marsh)

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
                choice = self.conf.misc["default_ai"]
            elif text.endswith(" (default)"):
                # If the user thought " (default)" was part of the name, strip.
                choice = text[:-len(" (default)")]
            else:
                choice = text
            try:
                if is_room:
                    ai_class = aihandler.get_manyonmany(choice)
                else:
                    ai_class = aihandler.get_oneonone(choice)
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

    def disconnected(self):
        """Try to reconnect to the xmpp network when disconnected.
        
        @TODO: Check if this actually works.
        
        """
        if not self.halt:
            c.stderr(u"DEBUG: xmpp: disconnected, trying to reconnect\n")
            self.connect()

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
            c.stderr(u"DEBUG: xmpp.Connection.exit called\n")

    def get_passwd(self, jid):
        """Get the password from the config or user.

        @param jid: The JID this password is for.
        @type jid: C{pyxmpp.jid.JID}

        """
        passw = self.conf.jabber["password"]
        if not passw:
            try:
                msg = u"Please enter the password for %s: " % unicode(jid)
                passw = c.getpass(msg)
            except (EOFError, IOError):
                passw = u""
                c.stdout_block("\n")
        return passw

    def handle_msg_chat(self, message):
        text = message.get_body()
        sender = px.JID(message.get_from())
        try:
            ai = self._parties[sender].get_AI()
            ai.handle(text)
        except KeyError:
            self.choose_AI(sender, message, is_room=False)
        if __debug__:
            c.stderr(u"DEBUG: chat: '%s' from '%s'\n" % (text, sender))
        return True

    def handle_msg_unsup(self, message):
        """Handle messages with an unsupported type.

        @TODO: handle error messages.

        """
        # The only <message type="normal"/> supported is an invitation to MUC.
        if message.get_type() == "normal":
            return self.handle_mucinvite(message)
        self._send(to_jid=message.get_from(), body=self.UNSUPPORTED_TYPE,
                stanza_type=message.get_type())
        if __debug__:
            msg = u"DEBUG: xmpp: unhandled: %s\n"
            c.stderr(msg % message.serialize().decode("utf-8"))
        return True

    def handle_mucinvite(self, message):
        """Handles incoming invitation to a MUC.

        See U{http://www.xmpp.org/extensions/xep-0045.html#invite} for more
        information.

        @TODO: use a supplied password when joining the room.

        """
        if __debug__:
            c.stderr(u"DEBUG: xmpp: invited to %s\n" % message.get_from())
        ns_map = {"mu": "http://jabber.org/protocol/muc#user"}
        nick = self.conf.misc["bot_nickname"]
        ai_list = self._create_AI_list()
        if not message.xpath_eval("/ns:message/mu:x/mu:invite", ns_map):
            # This stanza is not an invitation to a MUC.
            return False
        try:
            room_jid = px.JID(message.get_from().bare())
        except px.JIDError, e:
            c.stderr(u"WARNING: handle_mucinvite: %s\n" % unicode(e))
            return True
        if room_jid in self._parties:
            c.stderr(u"WARNING: already in %s\n" % unicode(room_jid))
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

    def leave_room(self, room):
        """Leave this room and remove it from the list of rooms.

        @param room: The room to leave.
        @type room: C{pyxmpp.jabber.muc.MucRoomState}

        """
        if __debug__:
            if not isinstance(room, px.jab.muc.MucRoomState):
                raise TypeError, "Room must be a MucRoomState."
        room.leave()
        del self._parties[room.room_jid.bare()]
        self.rooms.forget(room)

    def loop(self, timeout=1):
        """Simple looping that stops when self.halt is False."""
        while not self.halt:
            self.stream.loop_iter(timeout=timeout)
            self.idle()

    def run(self):
        self.connect()
        self.loop()
        self.disconnect()

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
        c.stdout(u"NOTICE: xmpp: logged in as %s\n" % unicode(self.jid))

    def state_change(*args):
        """Debug handler overwriting parent method."""
        c.stderr("DEBUG: state_change(%s, %s, %s)\n" % args)

class _MucEventHandler(px.jab.muc.MucRoomHandler):
    """Define handlers for events from MUC rooms.

    This includes everything from topic changes to incoming messages. Note that
    this class implements some hacks that make it virtually unsusable anywhere
    outside this module. Doing so is discouraged.

    @param connection: The xmpp connection that uses this handler.
    @type connection: L{Connection}
    @param room: The room this handler is instantiated for.
    @type room: L{parties.Group}

    """
    def __init__(self, connection, room):
        """Store some information about the room this handler belongs to."""
        if not isinstance(room, parties.Group):
            raise TypeError, "Wrong type room: %s" % type(room)
        px.jab.muc.MucRoomHandler.__init__(self)
        self.conn = connection
        self.room = room

    def message_received(self, sender, message):
        """Pass incoming message to appropriate AI module."""
        try:
            room_jid = px.JID(message.get_from()).bare()
        except JIDError:
            return True
        if sender is None or sender.same_as(self.room.mucstate.me):
            # Ignore messages from the conference server and this bot.
            return True
        text = message.get_body()
        if __debug__:
            c.stderr(u"DEBUG: xmpp: muc: %s: '%s'\n" %
                            (message.get_from(), text))
        # Rooms always have an instance stored in the _parties dictionary.
        room = self.conn._parties[room_jid]
        if room_jid in self.conn._aichoosers:
            self.conn.choose_AI(room_jid, message, is_room=True)
        else:
            ai = room.get_AI()
            member = room.get_participant(sender.nick)
            ai.handle(text, member)
        return True

    def nick_changed(self, user, old_nick, stanza):
        try:
            self.room.get_participant(old_nick).nick = user.nick
        except parties.NoSuchParticipantError:
            c.stderr(u"WARNING: unknown user %s entered %s.\n" %
                               (user.nick, self.room))
            self.room.add_participant(parties.GroupMember(self.room, user))
        return True
    nick_changed.__doc__ = px.jab.muc.MucRoomHandler.nick_changed.__doc__

    def user_joined(self, user, stanza):
        self.room.add_participant(parties.GroupMember(self.room, user))
        if __debug__:
            c.stderr(u"DEBUG: %s entered %s.\n" % (user.nick, self.room))
        return True
    user_joined.__doc__ = px.jab.muc.MucRoomHandler.user_joined.__doc__

    def user_left(self, user, stanza):
        if user.same_as(self.room.mucstate.me):
            self.conn.leave_room(self.room.mucstate)
        self.room.del_participant(parties.GroupMember(self.room, user))
