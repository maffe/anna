"""Connection handling of the MSN frontend."""

import getpass
import logging
import os
try:
    import threading as _threading
except ImportError:
    import dummy_threading as _threading
import time

import gobject
import pymsn

import aihandler
import config
from frontends import BaseConnection
from frontends.console.parties import Individual

_conf = config.get_conf_copy()
_def_ai_mom = aihandler.get_manyonmany(_conf.misc["default_ai"])
_def_ai_ooo = aihandler.get_oneonone(_conf.misc["default_ai"])
_logger = logging.getLogger("anna." + __name__)

def _log_call(func):
    """Decorator that logs a message before calling given function."""
    import itertools as i
    def n(*args, **kwargs):
        _logger.debug("%r(%s)", func, ", ".join(i.chain((repr(e) for e in
                args), ("%s=%r" % e for e in kwargs.iteritems()))))
        return func(*args, **kwargs)
    return n

def _log_meths(cls):
    """Create child-class that logs all calls to public methods."""
    class X(cls):
        pass
    for m in (a for a in dir(X) if a[0] != "_"):
        meth = getattr(X, m)
        if callable(meth):
            setattr(X, m, _log_call(meth))
    return X
_l = []
_e = pymsn.event
for i in (_e.AddressBookEventInterface, _e.ClientEventInterface,
        _e.ContactEventInterface, _e.ConversationEventInterface,
        _e.InviteEventInterface, _e.OfflineMessagesEventInterface):
    _l.append(_log_meths(i))

def _dec_con(contact):
    """Create a unicode object from a pymsn.profile.Contact instance."""
    return u"%s (%s)" % (contact.display_name.decode("utf-8"),
            contact.account.decode("utf-8"))

class _AddressBookHandler(pymsn.event.AddressBookEventInterface):
    def on_addressbook_messenger_contact_added(self, contact):
        _logger.debug(u"%s added this bot to its list.", _dec_con(contact))
        self._client.address_book.accept_contact_invitation(contact)

class _ClientHandler(pymsn.event.ClientEventInterface):
    def __init__(self, conn, *args, **kwargs):
        pymsn.event.ClientEventInterface.__init__(self, *args, **kwargs)
        # Just in case the parent class uses ._conn all of a sudden.
        self.__conn = conn

    def on_client_error(self, error_type, error):
        e_t = pymsn.event.ClientErrorType
        if error_type == e_t.AUTHENTICATION:
            _logger.error("Authentication failed.")
            self.__conn.disconnect()
        elif error_type in (e_t.NETWORK, e_t.PROTOCOL):
            _logger.error("Network/protocol failure.")
            self.__conn.disconnect()
        else:
            _logger.error("%s: %s.", error_type, error)

    def on_client_state_changed(self, state):
        if state == pymsn.event.ClientState.CLOSED:
            _logger.info("Connection to server closed.")
        elif state == pymsn.event.ClientState.AUTHENTICATED:
            _logger.info("Logged in.")
        elif state == pymsn.event.ClientState.OPEN:
            self._client.profile.display_name = _conf.misc["bot_nickname"]
            self._client.profile.presence = pymsn.profile.Presence.ONLINE

class _ContactHandler(pymsn.event.ContactEventInterface):
    def on_contact_memberships_changed(self, contact):
        if contact.memberships & pymsn.profile.Membership.PENDING:
            _logger.info(u"%s is still pending for approval.",
                    _dec_con(contact))
            self._client.address_book.accept_contact_invitation(contact)

class _ConversationHandler(pymsn.event.ConversationEventInterface):
    def on_conversation_message_received(self, sender, message):
        _logger.debug(u"Message from %s: %s" % (_dec_con(sender),
            message.content.decode("utf-8")))

class _InviteHandler(pymsn.event.InviteEventInterface):
    def __init__(self, *args, **kwargs):
        pymsn.event.InviteEventInterface.__init__(self, *args, **kwargs)
        # Keep a reference to prevent these poor handlers from being cleaned up
        # (pymsn uses weakrefs internally).
        self._convohandlers = []

    def on_invite_conversation(self, convo):
        _logger.debug("Invited to conversation.")
        self._convohandlers.append(_ConversationHandler(convo))

class Connection(BaseConnection, _threading.Thread):
    def __init__(self):
        _threading.Thread.__init__(self, name="MSN frontend")
        self._client = pymsn.Client((_conf.msn["server"], _conf.msn["port"]))
        self._handlers = [
                _AddressBookHandler(self._client),
                _ClientHandler(self, self._client),
                _ContactHandler(self._client),
                _InviteHandler(self._client),
                ]
        self._handlers.append(_l[0](self._client))
        self._handlers.append(_l[1](self._client))
        self._handlers.append(_l[2](self._client))
        #self._handlers.append(_l[3](self._client))
        self._handlers.append(_l[4](self._client))
        self._handlers.append(_l[5](self._client))

    def connect(self):
        # The connection will be closed when this is set to True.
        self.halt = False
        self.start()

    def disconnect(self):
        self.halt = True

    def run(self):
        context = gobject.MainLoop().get_context()
        # pymsn.Client.login wants utf-8 encoded byte strings.
        creds = [_conf.msn[e].encode("utf-8") for e in "username", "password"]
        self._client.login(*creds)
        while not self.halt:
            # Process all pending events.
            while context.iteration(False):
                pass
            time.sleep(0.3)
        self._client.logout()
