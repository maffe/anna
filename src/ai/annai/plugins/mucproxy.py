"""Sends all messages incoming in one groupchat through to others.

Also works for individuals. The syntax is as follows:

    load mucproxy <groupname> <yourname>

Groupname is the name of the group in this plugin: say individual A
joins groupname foo and then MUC B joins groupname foo too, they will
see eachothers messages. Individual C, though, who joins groupname bar,
will not.

You can see the list of participants by saying "names".

More information on U{the wiki
<https://0brg.net/anna/wiki/Mucproxy_plugin>}.

"""
try:
    import threading as _threading
except ImportError:
    import dummy_threading as _threading
import time

import config
from ai.annai.plugins import BasePlugin, PluginError

_conf = config.get_conf_copy()
# Always acquire _room_lock before doing ANYTHING with _rooms.
_room_lock = _threading.Lock()
_rooms = {}

class _Plugin(BasePlugin):
    def __init__(self, identity, args):
        if len(args) != 2:
            raise PluginError(u'Illegal syntax, see "about plugin mucproxy".')
        assert(isinstance(args[0], unicode))
        assert(isinstance(args[1], unicode))
        if u":" in args[1]:
            raise PluginError(u"Nickname may not contain colons (:).")
        self._identity = identity
        self._mucname = args[0]
        self._peername = args[1]
        _room_lock.acquire()
        try:
            if args[0] in _rooms:
                if any(map(lambda x: x[0] == args[1], _rooms[args[0]])):
                    raise PluginError(u"Name is taken.")
                if any(map(lambda x: x[1] == identity, _rooms[args[0]])):
                    raise PluginError(u"You can not join the same room twice.")
                _rooms[args[0]].append((args[1], identity))
                identity.send(u"Joined %s." % args[0])
            else:
                _rooms[args[0]] = [(args[1], identity)]
                identity.send(u"Created new room %s." % args[0])
        finally:
            _room_lock.release()

    def __unicode__(self):
        return u"MUC proxy for group " + self._mucname

    def _one_msg(self, msg, sender):
        """Process one message according to this plugin's rules."""
        assert(isinstance(msg, unicode))
        assert(isinstance(sender, unicode))
        _room_lock.acquire()
        try:
            for name, identity in _rooms[self._mucname]:
                if name != self._peername:
                    if msg.startswith(u"/me "):
                        identity.send(u"* %s %s" % (sender, msg[4:]))
                    else:
                        identity.send(u"<%s> %s" % (sender, msg))
        finally:
            _room_lock.release()

    def _process(self, msg, reply, sender):
        assert(isinstance(sender, unicode))
        if msg == "names":
            _room_lock.acquire()
            reply = u"Participants in %s:\n" % self._mucname
            reply += "\n".join(u"- %s (%s)" % e for e in _rooms[self._mucname])
            _room_lock.release()
            # Do not send the names command to other parties.
            return (msg, reply)
        if msg is not None:
            self._one_msg(msg, sender)
        if reply is not None:
            self._one_msg(reply, self._getmyname())
        return (msg, reply)

    def unloaded(self):
        _room_lock.acquire()
        try:
            room = _rooms[self._mucname]
            me = (self._peername, self._identity)
            assert(me in room)
            room.remove(me)
            assert(me not in room)
        finally:
            _room_lock.release()

class OneOnOnePlugin(_Plugin):
    def _getmyname(self):
        return _conf.misc["bot_nickname"]

    def process(self, message, reply):
        return self._process(message, reply, self._peername)

class ManyOnManyPlugin(_Plugin):
    def _getmyname(self):
        return u"%s:%s" % (self._peername, self._identity.get_mynick())

    def process(self, message, reply, sender, highlight):
        if highlight:
            message = "%s: %s" % (self._identity.get_mynick(), message)
        return self._process(message, reply, u"%s:%s" % (self._peername,
            sender.nick))
