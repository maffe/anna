"""Sends all messages incoming in one groupchat through to others.

Also works for individuals. The syntax is as follows:

    load mucproxy <groupname> <yourname>

Groupname is the name of the group in this plugin: say individual A
joins groupname foo and then MUC B joins groupname foo too, they will
see eachothers messages. Individual C, though, who joins groupname bar,
will not.

STRICTLY load this as the last plugin!

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
        self._identity = identity
        self._mucname = args[0]
        self._peername = args[1]
        _room_lock.acquire()
        if args[0] in _rooms:
            if any(map(lambda x: x[0] == identity, _rooms[args[0]])):
                raise PluginError(u"You can not join the same room twice.")
            _rooms[args[0]].append((identity, args[1]))
        else:
            _rooms[args[0]] = [(identity, args[1])]
        _room_lock.release()

    def __unicode__(self):
        return u"MUC proxy for group " + self._mucname

    def _one_msg(self, msg, sender):
        """Process one message according to this plugin's rules."""
        assert(isinstance(msg, unicode))
        assert(isinstance(sender, unicode))
        _room_lock.acquire()
        for identity, name in _rooms[self._mucname]:
            if name != self._peername:
                identity.send(u"<%s> %s" % (sender, msg))
        _room_lock.release()

    def _process(self, msg, reply, sender):
        assert(isinstance(sender, unicode))
        if msg == "names":
            _room_lock.acquire()
            reply = u", ".join(map(lambda x: x[1], _rooms[self._mucname]))
            _room_lock.release()
        if msg is not None:
            self._one_msg(msg, sender)
        if reply is not None:
            self._one_msg(reply, self._getmyname())
        return (msg, reply)

class OneOnOnePlugin(_Plugin):
    def _getmyname(self):
        return _conf.misc["bot_nickname"]

    def process(self, message, reply):
        return self._process(message, reply, self._peername)

class ManyOnManyPlugin(_Plugin):
    def _getmyname(self):
        return u"%s:%s" % (self._peername, self._identity.get_mynick())

    def process(self, message, reply, sender, highlight):
        return self._process(message, reply, u"%s:%s" % (self._peername,
            sender.nick))
