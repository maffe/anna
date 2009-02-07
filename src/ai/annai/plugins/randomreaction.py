"""This plugin allows the user to set random reactions."""

from __future__ import with_statement

import random
import re
try:
    import threading as _threading
except ImportError:
    import dummy_threading as _threading

from ai.annai.plugins import BasePlugin, PluginError
import ai.annai.plugins.reactions.plugin as rp

def _threadsafe(lock):
    '''Create a decorator that makes a function thread-safe.'''
    def deco(oldf):
        def newf(*args, **kwargs):
            with lock:
                return oldf(*args, **kwargs)
        return newf
    return deco

class _ReactionsDB(object):
    '''Thread-safe database interface for random reactions.

    All instances of this class share the same database.

    '''
    lock = _threading.Lock()
    db = {}
    @_threadsafe(lock)
    def add(self, hook, reactions):
        '''Add a new random reaction.

        @raise rp.ReactionExistsError: Existing reaction is overwritten.
        @param reactions: All reactions to this hook (note that this argument
            will be iterated over multiple times so a generator is not enough).
        @type reactions: iterable

        '''
        if hook in self.db:
            raise rp.ReactionExistsError, hook
        self.db[hook] = reactions

    @_threadsafe(lock)
    def get(self, hook):
        return random.choice(self.db[hook]) if hook in self.db else None

    @_threadsafe(lock)
    def delete(self, hook):
        try:
            del self.db[hook]
        except KeyError:
            raise rp.NoSuchReactionError, hook

class _Plugin(rp._Plugin):
    '''All instances can safely share the same thread-safe DB connection.'''
    _db = _ReactionsDB()
    REQ_ADD = re.compile(r'(global )?random reaction to (.*?) is \((.+\|.+)\)$',
            re.I | re.S)
    REQ_DEL = re.compile(r'forget (global )?random reaction to (.*)$',
            re.I | re.S)

    def __init__(self, party, args):
        if args:
            raise PluginError, u'No arguments allowed for %s.' % self
        self._msg_parsers = (
                self._handle_add,
                self._handle_delete,
                self._handle_react,
                )

    def __unicode__(self):
        return u'random reaction plugin'

    def _reaction_add(self, hook, rctn):
        '''Add a new reaction to the database.'''
        self._db.add(hook, rctn.split(u'|'))

    def _reaction_delete(self, hook):
        '''Delete this reaction from the database.'''
        self._db.delete(hook)

    def _reaction_get(self, hook):
        return self._db.get(hook)

class OneOnOnePlugin(_Plugin, rp.OneOnOnePlugin):
    pass

class ManyOnManyPlugin(_Plugin, rp.ManyOnManyPlugin):
    pass
