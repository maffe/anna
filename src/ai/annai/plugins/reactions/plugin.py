"""Very much like the factoids plugin, but for reactions.

See U{https://0brg.net/anna/wiki/Reactions_plugin} for more information.

"""

# Throughout the code the following convention is used: a 'reaction' is yielded
# whenever a 'hook' is encountered.

import re

import sqlalchemy as sa

from ai.annai.plugins import BasePlugin, PluginError
import communication as c
import config
import frontends

REQ_ADD = re.compile(u"(global )?reaction to (.*?) is (.*)", re.I | re.S)
REQ_DEL = re.compile(u"forget (global )?reaction to (.*)", re.I | re.S)
TYPE_DIRECT = 0
TYPE_GLOBAL = 1

db_uri = config.get_conf_copy().reactions_plugin["db_uri"]

class _Plugin(BasePlugin):
    """Common functions for both the OneOnOne and ManyOnMany plugins.
    
    This implements a state-machine for the type of reaction (direct or
    global). Whenever a _analyze_request function is called, it sets the
    instance variable _type if it hits. The _reaction_* functions use this
    variable to enter the proper value in the database.

    """
    def __init__(self, party, args):
        self._frmt = dict()
        # Functions to apply to incoming messages subsequently.
        self._msg_parsers = (
                self._handle_add,
                self._handle_delete,
                self._handle_react,
                )
        # Create the database if it doesn't exist.
        self._engine = sa.create_engine(db_uri)#, echo=True)
        self._md = sa.MetaData()
        self._table = sa.Table("reaction", self._md, 
                sa.Column("reaction_id", sa.Integer, primary_key=True),
                sa.Column("numreq", sa.Integer, sa.PassiveDefault('0'),
                    nullable=False),
                sa.Column("type", sa.Integer, nullable=False),
                # TODO: The hook is not unique because there can be two. A real
                # constraint should be formulated, though.
                sa.Column("hook", sa.String(512), nullable=False),
                sa.Column("reaction", sa.String(512), nullable=False),
                )
        self._md.bind = self._engine
        self._md.create_all(self._engine)

    def __unicode__(self):
        return u"reactions plugin"

    def _analyze_request_add(self, msg):
        """See if this message wants to set a new hook and reaction pair.

        @return: The factoid and its definition, or None if not applicable.
        @rtype: C{list} or C{None}

        """
        m = REQ_ADD.match(msg)
        if m is None:
            return None
        self._type = m.group(1) is not None and TYPE_GLOBAL or TYPE_DIRECT
        return (m.group(2), m.group(3))

    def _analyze_request_delete(self, msg):
        """See if this message was meant to delete.

        @return: The hook up for deletion, if applicable.
        @rtype: C{unicode} or C{None}

        """
        m = REQ_DEL.match(msg)
        if m is None:
            return None
        self._type = m.group(1) is not None and TYPE_GLOBAL or TYPE_DIRECT
        return m.group(2)

    def _reaction_add(self, hook, rectn):
        """Set the reaction to given hook.

        Stores the hook in lowercase to enable case-insensitive hook-matching.

        """
        if self._reaction_get(hook) is not None:
            raise ReactionExistsError, hook
        ins = self._table.insert(values=dict(
                hook=hook.lower(),
                reaction=rectn,
                type=self._type
                ))
        conn = self._engine.connect()
        conn.execute(ins)

    def _reaction_delete(self, hook):
        if self._reaction_get(hook) is None:
            raise NoSuchReactionError, hook
        conn = self._engine.connect()
        conn.execute(self._table.delete(self._table.c.hook==hook.lower()))

    def _reaction_get(self, hook):
        """Get the reaction to given hook.

        Uses the instance-variable C{_type} to determine the type of reaction
        to get. If this variable is C{None} type does not matter.

        @param hook: The hook to react to.
        @type hook: C{unicode}
        @return: The reaction (or None if it there is none).
        @rtype: C{unicode} or C{None}.

        """
        if __debug__:
            if not isinstance(hook, unicode):
                raise TypeError, "The argument must be a unicode object."
        if self._type is not None:
            type_check = self._table.c.type==self._type
        else:
            # No extra check needed.
            type_check = 1
        res = sa.select(
                columns=[self._table.c.reaction],
                whereclause=sa.and_(
                    self._table.c.hook==hook.lower(),
                    type_check),
                from_obj=self._table
                ).order_by(self._table.c.type.asc()).limit(1).execute()
                # Ordering it by type selects the DIRECT reaction first if
                # there are two available.
        row = res.fetchone()
        res.close()
        if row is None:
            return None
        else:
            return row[self._table.c.reaction]

    # These three methods must be overridden in subclasses!

    def _handle_add(self, message):
        """See if the sender wants to add a reaction."""
        pass

    def _handle_delete(self, message):
        """See if the sender wants to delete reaction."""
        pass

    def _handle_react(self, message):
        """Determine if this message is a hook for a reaction.

        @return: The reaction to the hook, if applicable.
        @rtype: C{unicode} or C{None}

        """
        pass

    def process(self, message, reply, sender=None, highlight=None):
        """Determine if the message has anything to do with reactions.

        Takes apropriate action in respective cases and returns a response. If
        a previous plugin already created any kind of answer this plugin does
        not do anything (it acts like a "last resort" plugin, only for cases
        nothing else matched).

        This ignores empty messages on purpose to prevent people
        "ghost-spamming" a chatroom by setting an annoying reaction to empty
        messages. These messages are not always very obvious and thus it might
        seem the bot is going wild for no reason.

        """
        if reply is not None or not message:
            return (message, reply)

        cleanmsg = message.strip()
        # State-machine for highlight status and sendertoo.
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

class OneOnOnePlugin(_Plugin):
    def __init__(self, peer, args):
        _Plugin.__init__(self, peer, args)
        self._frmt["user"] = unicode(peer)

    def _handle_add(self, message):
        result = self._analyze_request_add(message)
        if result is None:
            return None
        hook, reaction = result
        try:
            self._reaction_add(hook, reaction)
            return u"k"
        except ReactionExistsError:
            existing = self._reaction_get(hook)
            assert(existing is not None)
            if reaction == existing:
                return u"tell me something new"
            else:
                return u"but.. when you say %s I say %s :s" % (hook, existing)

    def _handle_delete(self, message):
        hook = self._analyze_request_delete(message)
        if hook is not None:
            try:
                self._reaction_delete(hook)
                return u"k"
            except NoSuchReactionError:
                return u"I don't even know what to say to that..."

    def _handle_react(self, message):
        self._type = None
        reaction = self._reaction_get(message)
        return reaction is not None and reaction or None

class ManyOnManyPlugin(_Plugin):
    def __init__(self, room, args):
        _Plugin.__init__(self, room, args)
        self._frmt["room"] = unicode(room)

    def _handle_add(self, message):
        result = self._analyze_request_add(message)
        if result is None:
            return None
        hook, reaction = result
        try:
            self._reaction_add(hook, reaction)
            return u"k"
        except ReactionExistsError:
            existing = self._reaction_get(hook)
            assert(existing is not None)
            if reaction == existing:
                return u"tell me something new"
            else:
                return u"but.. when you say %s I say %s :s" % (hook, existing)

    def _handle_delete(self, message):
        hook = self._analyze_request_delete(message)
        if hook is not None:
            try:
                self._reaction_delete(hook)
                return u"k"
            except NoSuchReactionError:
                return u"I don't even know what to say to that..."

    def _handle_react(self, message):
        """If highlighted ignore type, else only fetch global reactions."""
        self._type = not self.highlight and TYPE_GLOBAL or None
        reaction = self._reaction_get(message)
        self._frmt["user"] = unicode(self.sender.nick)
        if reaction is None:
            return None
        else:
            try:
                reaction = reaction % self._frmt
            except (KeyError, TypeError, ValueError), e:
                self._reaction_delete(message)
                return u'This reaction was broken ("%r"). I deleted it.' % e
            return reaction

class ReactionExistsError(Exception):
    """Raised when an existing reaction is tried to be overwritten."""
    def __init__(self, hook):
        assert(isinstance(hook, unicode))
        self.hook = hook
    def __str__(self):
        return "There is already a reaction to '%s'." % \
                                    self.hook.encode("ascii", "replace")
    def __unicode__(self):
        return u"There is already a reaction to '%s'." % self.hook

class NoSuchReactionError(Exception):
    """Raised when there is no reaction to given hook."""
    def __init__(self, hook):
        assert(isinstance(hook, unicode))
        self.hook = hook
    def __str__(self):
        return "No reaction to '%s'." % self.hook.encode("ascii", "replace")
    def __unicode__(self):
        return u"No reaction to '%s'." % self.hook
