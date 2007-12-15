"""Connect to the xmpp network and define connection handlers."""

import getpass
import sys

import pyxmpp.all as px
import pyxmpp.jabber.all as pxj
px.jab = pxj
del pxj

import aihandler
import config
from frontends.xmpp import parties
from frontends import BaseConnection

class Connection(px.jab.Client, BaseConnection):
    """A talk-specific connection with the other party.

    Controls the communication by providing methods for sending messages and
    setting handlers for incoming messages.

    """
    UNSUPPORTED_TYPE = "Sorry, this type of messages are not supported."""
    CHOOSE_AI = "Please choose an AI from the list first:\n%s"
    NO_SUCH_AI = "No such AI. Please try again."

    def __init__(self, jid=None, password=None):
        self.conf = config.get_conf_copy()
        # Everybody waiting to be assigned an AI instance.
        self._aichoosers = []
        # List of party instances known to the bot. Maps JIDs to Individuals.
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

    def choose_AI(self, party, message):
        """Handles conversations with this party when no AI is assigned yet.
        
        The first argument is an pyxmpp.JID instance of the party starting a
        new conversation, the second one is the message they sent. For now this
        can only be used for PMs, not fur MUCs. TODO: fix.
        
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
                choice = choice[:-len(" (default)")]
            else:
                choice = text
            try:
                ai_class = aihandler.get_oneonone(text)
            except ValueError:
                msg = "\n\n".join((self.NO_SUCH_AI, self._create_AI_list()))
            else:
                idnty = parties.Individual(party, self.stream)
                idnty.set_AI(ai_class(idnty))
                self._parties[party] = idnty
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
        print "XMPP frontend started, looping."
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
            print >> sys.stderr, "DEBUG: xmpp.Connection().exit() called"

    def get_creds(self):
        """Get the JID and password from the config or user."""
        jab_conf = self.conf.jabber
        args = (jab_conf["user"], jab_conf["server"], jab_conf["resource"])
        jid = px.JID(*args)
        passw = self.conf.jabber["password"]
        if not passw:
            try:
                msg = u"Please enter the password for %s: " % unicode(jid)
                passw = getpass.getpass(msg.encode(sys.stdout.encoding))
                passw = passw.decode(sys.stdin.encoding)
            except EOFError:
                passw = u""
            except KeyboardInterrupt:
                passw = u""
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
            self.choose_AI(sender, message)
        if __debug__:
            msg = u"DEBUG: chat: '%s' from '%s'" % (text, sender)
            print >> sys.stderr, msg.encode(sys.stdout.encoding)
        return True

    def handle_msg_unsup(self, message):
        self._send(to_jid=message.get_from(), body=self.UNSUPPORTED_TYPE,
                stanza_type=message.get_type())
        if __debug__:
            msg = u"DEBUG: groupchat: '%s' from '%s'" % (text, sender)
            print >> sys.stderr, msg.encode(sys.stdout.encoding)
        return True

    def session_started(self):
        """Called by pyxmpp when the session has succesfully started."""
        # Priorities in PyXMPP are from low to high.
        self.stream.set_message_handler(typ="chat", priority=30,
                handler=self.handle_msg_chat)
        self.stream.set_message_handler(typ="normal", priority=70,
                handler=self.handle_msg_unsup)
        #self.stream.set_iq_get_handler("query", "jabber:iq:version",
        #                            handler=self.handle_version)

    def state_change(*args):
        """Debug handler overwriting parent method."""
        print >> sys.stderr, "DEBUG: state_change(%s, %s, %s)" % args
