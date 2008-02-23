"""Fetch a factoid.

Because this plugin is considered so "heavy" it acts SHY: if there is
already a reply constructed by one of the previous plugins, it exits
immediately.

@TODO: Implement low-level functions (self._get_factoid() etc).

"""
import sqlalchemy as sa

from ai.annai.plugins import BasePlugin, PluginError
import communication as c
import config
import frontends

db_uri = config.get_conf_copy().factoids_plugin["db_uri"]

def _init_db():
    """Create the database if it doesn't exist and return a MetaData object."""
    engine = sa.create_engine(db_uri)#, echo=True) # Extra debugging info.
    md = sa.MetaData()
    t_fac = sa.Table("factoid", md,
            sa.Column("factoid_id", sa.Integer, primary_key=True),
            sa.Column("reqnum", sa.Integer, nullable=False, default=0),
            sa.Column("object", sa.String(512), nullable=False),
            sa.Column("definition", sa.String(512), nullable=False),
            )
    md.bind = engine
    md.create_all(engine)
    return md

class _Plugin(BasePlugin):
    """Common functions for both the OneOnOne and ManyOnMany plugins."""
    def __init__(self, party, args):
        self.party = party
        self.md = _init_db()

    def __unicode__(self):
        return u"factoids plugin"

    def _get_factoid(self, obj):
        """Get the definition of given object.

        @param obj: The factoid to define.
        @type obj: C{unicode}
        @return: The definition (or None if it there is none).
        @rtype: C{unicode} or C{None}.

        """
        if __debug__:
            if not isinstance(obj, unicode):
                raise TypeError, "The argument must be a unicode object."
        table = self.md.tables["factoid"]
        res = sa.select(
                columns=[table.c.definition],
                whereclause=table.c.object == obj,
                from_obj=table
                ).execute()
        row = res.fetchone()
        res.close()
        if row is None:
            return None
        else:
            return row[table.c.definition]

    def _set_factoid(self, obj, definition):
        """Set the definition of given factoid."""
        c.stderr(u"DEBUG: not gonna remember: %s means %s.\n" % (obj, definition))

class OneOnOnePlugin(_Plugin):
    def __init__(self, identity, args):
        _Plugin.__init__(self, identity, args)
        self.ident = identity
        # Functions to apply to incoming messages subsequently.
        self._msg_parsers = (self.fetch, self.edit)

    def process(self, message, reply):
        """Determine if the message wants to know about or edit a factoid.

        Takes apropriate action in respective cases and returns a response. If
        a previous plugin already created any kind of answer this plugin does
        not do anything (it acts like a "last resort" plugin, only for cases
        nothing else matched).

        """
        if not reply is None:
            return (message, reply)

        cleanmsg = message.strip()
        for parser in self._msg_parsers:
            result = parser(cleanmsg)
            if result is not None:
                assert(isinstance(result, unicode))
                return (message, result)
        # None of the parsers felt the need to answer to this message.
        return (message, reply)

    def fetch(self, message):
        """Determine if this message wants the definition of a factoid.

        @return: The definition of the factoid that was requested.
        @rtype: C{unicode} or C{None}

        """
        result = None
        if message[:8].lower() == "what is ":
            result = self._get_factoid(message[8:].rstrip(" ?"))
        elif message[:7].lower() == "what's ":
            result = self._get_factoid(message[7:].rstrip(" ?"))
        elif message[:17].lower() == "do you know what " \
                and message.rstrip(" ?").endswith(" is"):
            result = self._get_factoid(message.rstrip(" ?")[17:-3])
        elif message.endswith("?"):
            result = self._get_factoid(message.rstrip(" ?"))
        else:
            return None

        # result holds the return value of a _get_factoid() call.
        return result is None and u"Idk.. can you tell me?" or result

    def edit(self, message):
        """See if the sender wanted to change a factoid.

        @TODO: check for unexistant factoid on deletion.

        """
        # forget factoid
        if message[:7].lower() == "forget ":
            object = message[7:]
            if object.startswith("what ") and object.endswith(" is"):
                object = object[5:-3]
            del_factoid(object)
            return u"k."

        #add factoid
        if not " is " in message:
            return None

        object, definition = [e.strip() for e in message.split(" is ", 1)]

        result = set
        try:
            self._set_factoid(object, definition)
            return u"k"
        except FactoidExistsError:
            existing = self._get_factoid(object)
            if definition == existing:
                return u"I know"
            else:
                return u"but... but... %s is %s" % (object, existing)

class ManyOnManyPlugin(_Plugin):
    def __init__(self, room, args):
        """Tell the room that this plugin is unavailable for now."""
        raise PluginError, u"This plugin is only available for PM."
    def process(self, message, reply, sender):
        assert(False)

class FactoidExistsError(Exception):
    """Raised if an existing factoid is tried to be overwritten."""
    def __init__(self, obj):
        assert(isinstance(obj, unicode))
        self.obj = obj
    def __unicode__(self):
        return u"Factoid '%s' already exists." % self.obj
