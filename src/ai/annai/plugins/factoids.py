"""Fetch a factoid.

Because this plugin is considered so "heavy" it acts SHY: if there is
already a reply constructed by one of the previous plugins (ie:
"if reply is not None"), it exits immediately.

@TODO: Implement low-level functions (get_factoid() etc).

"""
import sqlalchemy as sa

from ai.annai.plugins import BasePlugin
import frontends

class _Plugin(BasePlugin):
    """Common functions for both the OneOnOne and ManyOnMany plugins.

    @TODO: Design a clean way to handle databasing.

    """
    def __init__(self):
        self.db = sa.create_engine("sqlite:///factoids.db")
        self.metadata = sa.BoundMetaData(self.db)
        if __debug__:
            # TODO: thread-safe?
            self.metadata.engine.echo = True
        self.factoids = sa.Table('factoid', self.metadata, autoload=True)

    def __unicode__(self):
        return "factoids plugin"

    def _get_factoid(obj):
        """Get the definition of given object.

        @return: The definition (or None if it there is none).
        @rtype: C{unicode} or C{None}.

        """
        if __debug__:
            if not isinstance(obj, unicode):
                raise TypeError, "The argument must be a unicode object."
        table = self.factoids
        r = table.select(table.c.object==obj).execute()
        r.fetchone()

class OneOnOnePlugin(_Plugin):
    def __init__(self, identity):
        _Plugin.__init__(self)
        self.ident = identity

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
        result = self.edit(cleanmsg)
        if result is not None:
            assert(isinstance(result, unicode))
            return (message, result)
        else:
            return (message, self.fetch(cleanmsg))

    def fetch(self, message):
        """Determine if this message wants the definition of a factoid.

        @return: The definition of the factoid that was requested.
        @rtype: C{unicode} or C{None}

        """
        result = None
        if message[:8].lower() == "what is ":
            result = get_factoid(message[8:].rstrip(" ?"))
        elif message[:7].lower() == "what's ":
            result = get_factoid(message[7:].rstrip(" ?"))
        elif message[:17].lower() == "do you know what " \
                and message.rstrip(" ?").endswith(" is"):
            result = get_factoid(message.rstrip(" ?")[17:-3])
        elif result.endswith("?"):
            result = get_factoid(message.rstrip(" ?"))
            if result is None:
                return None

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
            set_factoid(object, definition)
            return u"k"
        except FactoidExistsError:
            existing = get_factoid(object)
            if definition == existing:
                return u"I know"
            else:
                return u"but... but... %s is %s" % (object, existing)

class ManyOnManyPlugin(_Plugin):
    def __init__(self, room):
        """Tell the room that this plugin is unavailable for now."""
        room.send(u"The factoids plugin does not (yet) work for groupchats.")
    def process(self, message, reply, sender):
        return (message, reply)
