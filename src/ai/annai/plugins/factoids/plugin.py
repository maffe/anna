"""Manipulate the factoids database.

Because this plugin is considered so "heavy" it acts SHY: if there is
already a reply constructed by one of the previous plugins, it exits
immediately.

See U{https://0brg.net/anna/wiki/Factoids_plugin} for more info.

"""
import sqlalchemy as sa

from ai.annai.plugins import BasePlugin, PluginError
import communication as c
import config
import frontends

db_uri = config.get_conf_copy().factoids_plugin["db_uri"]

class _Plugin(BasePlugin):
    """Common functions for both the OneOnOne and ManyOnMany plugins."""
    def __init__(self, party, args):
        self.party = party
        # Functions to apply to incoming messages subsequently.
        self._msg_parsers = (
                self._handle_fetch,
                self._handle_add,
                self._handle_delete,
                )
        # Create the database if it doesn't exist.
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

    def __unicode__(self):
        return u"factoids plugin"

    def _analyze_request_add(self, msg):
        """See if this message was meant to add a factoid.

        @return: The factoid and its definition, or None if not applicable.
        @rtype: C{list} or C{None}

        """
        if " is " not in msg:
            return None
        else:
            return [e.strip() for e in msg.split(" is ", 1)]

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
        if msg[:8].lower() == "what is ":
            return msg[8:].rstrip(" ?")
        elif msg[:7].lower() == "what's ":
            return msg[7:].rstrip(" ?")
        elif msg[:17].lower() == "do you know what " \
                and msg.rstrip(" ?").endswith(" is"):
            return msg.rstrip(" ?")[17:-3]
        elif msg.endswith("?"):
            return msg.rstrip(" ?")
        else:
            return None

    def _factoid_add(self, obj, defin):
        """Set the definition of given factoid."""
        if self._factoid_get(obj) is not None:
            raise FactoidExistsError, obj
        ins = self._table.insert(values=dict(object=obj, definition=defin))
        conn = self._engine.connect()
        conn.execute(ins)

    def _factoid_delete(self, obj):
        if self._factoid_get(obj) is None:
            raise NoSuchFactoidError, obj
        conn = self._engine.connect()
        conn.execute(self._table.delete(self._table.c.object==obj))

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
                whereclause=(self._table.c.object==obj),
                from_obj=self._table
                ).execute()
        row = res.fetchone()
        res.close()
        if row is None:
            return None
        else:
            return row[self._table.c.definition]

    # These three methods must be overridden in subclasses!

    def _handle_add(self, message):
        """See if the sender wants to add a factoid."""
        pass

    def _handle_delete(self, message):
        """See if the sender wants to delete factoid."""
        pass

    def _handle_fetch(self, message):
        """Determine if this message wants the definition of a factoid.

        @return: The definition of the factoid that was requested.
        @rtype: C{unicode} or C{None}

        """
        pass

    def process(self, message, reply, sender=None, highlight=None):
        """Determine if the message wants to know about or edit a factoid.

        Takes apropriate action in respective cases and returns a response. If
        a previous plugin already created any kind of answer this plugin does
        not do anything (it acts like a "last resort" plugin, only for cases
        nothing else matched).

        """
        if not reply is None:
            return (message, reply)

        cleanmsg = message.strip()
        # State-machine :)
        self.highlight = highlight
        for parser in self._msg_parsers:
            result = parser(cleanmsg)
            if result is not None:
                assert(isinstance(result, unicode))
                del self.highlight
                return (message, result)
        # None of the parsers felt the need to answer to this message.
        del self.highlight
        return (message, reply)

class OneOnOnePlugin(_Plugin):
    def _handle_add(self, message):
        result = self._analyze_request_add(message)
        if result is None:
            return None
        object_, definition = result
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

    def _handle_delete(self, message):
        obj = self._analyze_request_delete(message)
        if obj is not None:
            try:
                self._factoid_delete(obj)
                return u"k"
            except NoSuchFactoidError:
                return u"I don't even know what that means..."

    def _handle_fetch(self, message):
        obj = self._analyze_request_fetch(message)
        if obj is None:
            return None
        definition = self._factoid_get(obj)
        return definition is None and u"Idk.. can you tell me?" or definition

class ManyOnManyPlugin(_Plugin):
    def _handle_add(self, message):
        if not self.highlight:
            return None
        result = self._analyze_request_add(message)
        if result is None:
            return None
        object_, definition = result
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

    def _handle_delete(self, message):
        if not self.highlight:
            return None
        obj = self._analyze_request_delete(message)
        if obj is not None:
            try:
                self._factoid_delete(obj)
                return u"k"
            except NoSuchFactoidError:
                return u"I don't even know what that means..."

    def _handle_fetch(self, message):
        obj = self._analyze_request_fetch(message)
        if obj is None:
            return None
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
