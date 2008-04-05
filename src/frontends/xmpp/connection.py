"""Connect to the xmpp network and define connection handlers.

@TODO: Display better error message when connection/auth fails.

"""
from socket import error as socket_error
try:
    import threading as _threading
except ImportError:
    import dummy_threading as _threading
import time

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

#: Number of seconds to wait between reconnection attempts when disconnected.
_RECONNECT_INTERVAL = 5

class Connection(px.jab.Client, _threading.Thread):
    """Threaded connection to an XMPP server.

    @ivar _rooms: Manager of all MUC rooms instantiated in this session.
    @type _rooms: C{pyxmpp.jabber.muc.MucRoomManager}
    @ivar _parties: Dictionary holding all instantiated parties.
    @type _parties: C{dict}

    """
    #: Standard reply to all incoming messages of unsupported type.
    UNSUPPORTED_TYPE = u"Sorry, this type of messages is not supported."""
    def __init__(self, **kwargs):
        _threading.Thread.__init__(self, name="xmpp frontend")
        self.conf = config.get_conf_copy()
        if "jid" not in kwargs:
            jab_conf = self.conf.xmpp
            args = (jab_conf["user"], jab_conf["server"], jab_conf["resource"])
            kwargs["jid"] = px.JID(*args)
        if "password" not in kwargs:
            kwargs["password"] = self.get_passwd(kwargs["jid"])
        px.jab.Client.__init__(self, **kwargs)

        # List of party instances known to the bot. Maps JIDs to Identities.
        self._parties = {}
        # The connection will be closed when this is set to True.
        self.halt = False

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

    def connect(self):
        """Overrides C{pyxmpp.jabber.Client.connect} for the sake of API."""
        self.start()

    def disconnect(self):
        """Overrides C{pyxmpp.jabber.Client.disconnect} for the sake of API."""
        self.halt = True

    def disconnected(self):
        """Try to reconnect to the xmpp network when disconnected."""
        for room in self._rooms.rooms.values():
            self.leave_room(room)
        while not self.halt:
            c.stderr(u"DEBUG: xmpp: disconnected, trying to reconnect\n")
            try:
                px.jab.Client.connect(self)
                # If the reconnection was succesful, stop retrying.
                break
            except socket_error, e:
                c.stderr(u"DEBUG: xmpp: error: %s, retrying\n" % e)
                time.sleep(_RECONNECT_INTERVAL)

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
        passw = self.conf.xmpp["password"]
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
        if __debug__:
            c.stderr(u"DEBUG: xmpp: pm: '%s' from '%s'\n" % (text, sender))
        try:
            peer = self._parties[sender]
        except KeyError:
            # This is the first message from this peer.
            peer = parties.Individual(sender, self.stream)
            self._parties[sender] = peer
            def_AI = self.conf.misc["default_ai"]
            peer.set_AI(aihandler.get_oneonone(def_AI)(peer))
        peer.get_AI().handle(text)
        return True

    def handle_msg_unsup(self, message):
        """Handle messages with an unsupported type.

        @TODO: handle error messages.

        """
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
        ns_map = {"mu": "http://jabber.org/protocol/muc#user"}
        nick = self.conf.misc["bot_nickname"]
        if not message.xpath_eval("/ns:message/mu:x/mu:invite", ns_map):
            # This stanza is not an invitation to a MUC.
            return False
        if __debug__:
            c.stderr(u"DEBUG: xmpp: invited to %s\n" % message.get_from())
        try:
            room_jid = message.get_from().bare()
        except px.JIDError, e:
            c.stderr(u"WARNING: handle_mucinvite: %s\n" % unicode(e))
            return True
        if unicode(room_jid) in self._rooms.rooms:
            c.stderr(u"WARNING: already in %s\n" % unicode(room_jid))
            return True
        room = parties.Group(room_jid, self.stream)
        handler = _MucEventHandler(self, room)
        self._rooms.join(room_jid, nick, handler, history_maxstanzas=0)
        room.mucstate = self._rooms.rooms[unicode(room_jid)]
        def_AI = self.conf.misc["default_ai"]
        room.set_AI(aihandler.get_manyonmany(def_AI)(room))
        room.send(u"Hi, I am a chatbot. Thanks for inviting me here.")
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
        self._rooms.forget(room)

    def loop(self, timeout=1):
        """Simple looping that stops when self.halt is False."""
        try:
            while not self.halt:
                self.stream.loop_iter(timeout=timeout)
                self.idle()
        except socket_error, e:
            c.stderr(u"DEBUG: Connection error: %s.\n" % e)
            c.stdout(u"WARNING: Connection error, trying to reconnect.\n")
            self.disconnected()

    def run(self):
        px.jab.Client.connect(self)
        self.loop()
        self.exit()

    def session_started(self):
        """Called by pyxmpp when the session has succesfully started."""
        # Priorities in PyXMPP are from low to high.
        self.stream.set_message_handler(typ="chat", priority=30,
                handler=self.handle_msg_chat)
        self.stream.set_message_handler(typ="normal", priority=50,
                handler=self.handle_mucinvite)
        self.stream.set_message_handler(typ="normal", priority=70,
                handler=self.handle_msg_unsup)
        #self.stream.set_iq_get_handler("query", "jabber:iq:version",
        #                            handler=self.handle_version)
        self._rooms = px.jab.muc.MucRoomManager(self.stream)
        self._rooms.set_handlers(priority=40)
        c.stdout(u"NOTICE: xmpp: logged in as %s\n" % unicode(self.jid))

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
        except JIDError, e:
            c.stderr(u"WARNING: xmpp: malformed muc JID: %s\n" % e)
            return False
        if sender is None or sender.same_as(self.room.mucstate.me):
            # Ignore messages from the conference server and this bot.
            return True
        text = message.get_body()
        if __debug__:
            c.stderr(u"DEBUG: xmpp: muc: %s: '%s'\n" %
                            (message.get_from(), text))
        ai = self.room.get_AI()
        try:
            member = self.room.get_participant(sender.nick)
        except parties.NoSuchParticipantError, e:
            c.stderr(u"NOTICE: xmpp: muc: ignoring: %s\n" % e)
        else:
            ai.handle(text, member)
        return True
    message_received.__doc__ = \
            px.jab.muc.MucRoomHandler.message_received.__doc__

    def nick_changed(self, user, old_nick, stanza):
        try:
            self.room.get_participant(old_nick).nick = user.nick
        except parties.NoSuchParticipantError:
            c.stderr(u"WARNING: unknown user %s changed nick in %s (added)\n" %
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
        try:
            self.room.del_participant(parties.GroupMember(self.room, user))
        except parties.NoSuchParticipantError, e:
            c.stderr(u"NOTICE: xmpp: muc: unknown prtcipant leaving: %s\n" % e)
        if __debug__:
            c.stderr(u"DEBUG: %s left %s.\n" % (user.nick, self.room))
    user_left.__doc__ = px.jab.muc.MucRoomHandler.user_left.__doc__
