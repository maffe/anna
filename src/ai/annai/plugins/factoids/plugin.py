"""Manipulate the factoids database.

Because this plugin is considered so "heavy" it acts SHY: if there is
already a reply constructed by one of the previous plugins, it exits
immediately.

See U{https://0brg.net/anna/wiki/Factoids_plugin} for more info.

"""
import random
import re
try:
    import threading as _threading
except ImportError:
    import dummy_threading as _threading

import sqlalchemy as sa

from ai.annai.plugins import BasePlugin, PluginError
import communication as c
import config

class _Plugin(BasePlugin):
    """Common functions for both the OneOnOne and ManyOnMany plugins."""
    #: Regexp to match for factoid requests. The first non-empty group will be
    #: taken as the requested object.
    _rex_get = re.compile("|".join((
        ur"^(?:what|where|who)(?: i|['\u2019])s (.*?)\?*$", # what/where/who is
        r"^(.*?)\?+$" # Anything that ends with a question mark.
        )))
    def __init__(self, party, args):
        self._party = party
        # Functions to apply to incoming messages subsequently.
        self._msg_parsers = (
                self._handle_annoy,
                self._handle_fetch,
                self._handle_add,
                self._handle_delete,
                )
        # Create the database if it doesn't exist.
        db_uri = config.get_conf_copy().factoids_plugin["db_uri"]
        self._engine = sa.create_engine(db_uri)#, echo=True)
        self._md = sa.MetaData()
        self._table = sa.Table("factoid", self._md, 
                sa.Column("factoid_id", sa.Integer, primary_key=True),
                sa.Column("numreq", sa.Integer, sa.PassiveDefault('0'),
                    nullable=False),
                sa.Column("object", sa.String(512), nullable=False,
                    unique=True),
                sa.Column("definition", sa.String(512), nullable=False),
                )
        self._md.bind = self._engine
        self._md.create_all(self._engine)
        # Seconds between subsequent calls to _annoy()
        self._aintrv = 300
        # Lock must be acquired before manipulating the annoy timer.
        self._annoy_lock = _threading.Lock()

    def __unicode__(self):
        return u"factoids plugin"

    def _annoy(self):
        """Sends random factoid/definition pairs to the other party.

        Selecting a random row from the table is currently done very
        inefficiently. Portability amongst different DB engines is currently
        considered more important than efficiency. The interval is the amount
        of seconds to wait between subsequent sends, approximately (real
        waiting time is between 80% and 120% of given interval).

        """
        self._annoy_lock.acquire()
        if hasattr(self, "_annoy_timer"):
            self._annoy_timer.cancel()
        res = sa.select(columns=[self._table.c.factoid_id]).execute()
        rand_id = random.choice(res.fetchall())
        res.close()
        res = sa.select(
                columns=[self._table.c.object, self._table.c.definition],
                whereclause=(self._table.c.factoid_id==rand_id[0]),
                from_obj=self._table
                ).execute()
        row = res.fetchone()
        res.close()
        self._party.send(u" is ".join(row))
        # Create a random number close to the given interval.
        intr = random.randint(int(self._aintrv * 0.8), int(self._aintrv * 1.2))
        self._annoy_timer = _threading.Timer(intr, self._annoy)
        self._annoy_timer.setDaemon(True)
        self._annoy_timer.start()
        self._annoy_lock.release()

    def _analyze_request_add(self, msg):
        """See if this message was meant to add a factoid.

        @return: The factoid and its definition, or None if not applicable.
        @rtype: C{tuple} or C{None}

        """
        if " is " not in msg:
            return None
        else:
            object_, definition = (e.strip() for e in msg.split(" is ", 1))
            if object_.lower().startswith(u"no, "):
                object_ = object_[len(u"no, "):]
            return (object_, definition)

    def _analyze_request_delete(self, msg):
        """See if this message was meant to delete a factoid.

        @return: The factoid up for deletion, if applicable.
        @rtype: C{unicode} or C{None}

        """
        # forget factoid
        if msg[:7].lower() == "forget ":
            object_ = msg[7:]
            if object_.startswith("what ") and object_.endswith(" is"):
                object_ = object_[5:-3]
            return object_.strip()
        else:
            return None

    def _analyze_request_fetch(self, msg):
        """See if this message was meant to fetch a factoid.

        @return: The requested factoid (not definition) if applicable.
        @rtype: C{unicode} or C{None}

        """
        match = self._rex_get.search(msg.lower())
        if match is None:
            return None
        else:
            # Raises an IndexError if all groups are None. Should never happen.
            return [g for g in match.groups() if g is not None][0].strip()

    def _factoid_add(self, obj, defin):
        """Set the definition of given factoid.

        Stores the object in lower-case to allow case-insensitive fetching.

        """
        if self._factoid_get(obj) is not None:
            raise FactoidExistsError, obj
        ins = self._table.insert(values=dict(object=obj.lower(),
            definition=defin))
        conn = self._engine.connect()
        conn.execute(ins)

    def _factoid_delete(self, obj):
        if self._factoid_get(obj) is None:
            raise NoSuchFactoidError, obj
        conn = self._engine.connect()
        conn.execute(self._table.delete(self._table.c.object==obj.lower()))

    def _factoid_get(self, obj):
        """Get the definition of given object.

        @param obj: The factoid to define.
        @type obj: C{unicode}
        @return: The definition (or None if it there is none).
        @rtype: C{unicode} or C{None}.

        """
        if __debug__:
            if not isinstance(obj, unicode):
                raise TypeError, "The argument must be a unicode object."
        res = sa.select(
                columns=[self._table.c.definition],
                whereclause=(self._table.c.object==obj.lower()),
                from_obj=self._table
                ).execute()
        row = res.fetchone()
        res.close()
        if row is None:
            return None
        else:
            return row[self._table.c.definition]

    def _handle_annoy(self, message):
        """Interface for toggling annoying on/off."""
        if not self.highlight:
            return None
        elif message.lower() == "annoy":
            self._annoy()
            return u""
        elif message.lower() == "stop annoying":
            try:
                self._annoy_lock.acquire()
                self._annoy_timer.cancel()
                del self._annoy_timer
                self._annoy_lock.release()
                return u"k"
            except AttributeError:
                self._annoy_lock.release()
                return u"I wasn't doing anything.."
        elif message.lower().startswith("annoy rate "):
            try:
                intrv = int(message[len("annoy rate "):].strip())
            except ValueError:
                return None
            if intrv < 1:
                return u"Interval too low."
            self._aintrv = intrv
            self._annoy()
            return u"Interval updated."

    def _handle_delete(self, message):
        """See if the sender wants to delete factoid."""
        if not self.highlight:
            return None
        object_ = self._analyze_request_delete(message)
        if object_ is not None:
            try:
                self._factoid_delete(object_)
                return u"k"
            except NoSuchFactoidError:
                return u"I don't even know what that means..."

    def _handle_add(self, message):
        """See if the sender wants to add a factoid."""
        if not self.highlight:
            return None
        result = self._analyze_request_add(message)
        if result is None:
            return None
        object_, definition = result
        if message.lower().startswith(u"no, "):
            # Sender wants to overwrite meaning of this object.
            try:
                self._factoid_delete(object_)
            except NoSuchFactoidError, e:
                pass
        try:
            self._factoid_add(object_, definition)
            return u"k"
        except FactoidExistsError:
            existing = self._factoid_get(object_)
            assert(existing is not None)
            if definition == existing:
                return u"I know"
            else:
                return u"but... but... %s is %s" % (object_, existing)

    # This method should be overwritten.

    def _handle_fetch(self, message):
        """Determine if this message wants the definition of a factoid.

        Should be overwritten by child classes.

        @return: The definition of the factoid that was requested.
        @rtype: C{unicode} or C{None}

        """
        pass

    def process(self, message, reply, sender=None, highlight=True):
        """Determine if the message wants to know about or edit a factoid.

        Takes apropriate action in respective cases and returns a response. If
        a previous plugin already created any kind of answer this plugin does
        not do anything (it acts like a "last resort" plugin, only for cases
        nothing else matched).

        The highlight keyword is kind of a hack: it is always either True or
        False if this plugin is loaded as a ManyOnMany. If it's None that means
        this plugin is a OneOnOne, thus we can act as if highlighted in a MUC.

        """
        if not reply is None:
            return (message, reply)

        cleanmsg = message.strip()
        # State-machine :)
        self.highlight = highlight
        self.sender = sender
        for parser in self._msg_parsers:
            result = parser(cleanmsg)
            if result is not None:
                assert(isinstance(result, unicode))
                del self.highlight, self.sender
                return (message, result)
        # None of the parsers felt the need to answer to this message.
        del self.highlight, self.sender
        return (message, reply)

    def unloaded(self):
        self._annoy_lock.acquire()
        if hasattr(self, "_annoy_timer"):
            self._annoy_timer.cancel()
        self._annoy_lock.release()

class OneOnOnePlugin(_Plugin):
    def _handle_fetch(self, message):
        obj = self._analyze_request_fetch(message)
        if obj is None:
            return None
        definition = self._factoid_get(obj)
        return definition is None and u"Idk.. can you tell me?" or definition

class ManyOnManyPlugin(_Plugin):
    def _handle_fetch(self, message):
        assert(self.sender is not None)
        obj = self._analyze_request_fetch(message)
        if obj is None:
            return None
        elif obj == "me":
            obj = self.sender.nick
        definition = self._factoid_get(obj)
        if definition is not None:
            return definition
        elif self.highlight:
            return u"Idk.. can you tell me?"
        else:
            return None

class FactoidExistsError(Exception):
    """Raised when an existing factoid is tried to be overwritten."""
    def __init__(self, obj):
        assert(isinstance(obj, unicode))
        self.obj = obj
    def __unicode__(self):
        return u"Factoid '%s' already exists." % self.obj

class NoSuchFactoidError(Exception):
    """Raised when an unexistant factoid is addressed."""
    def __init__(self, obj):
        assert(isinstance(obj, unicode))
        self.obj = obj
    def __unicode__(self):
        return u"Factoid '%s' does not exist." % self.obj
