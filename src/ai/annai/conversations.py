"""The conversation classes for the annai AI module."""

import random
import re
import sys

import ai
from ai.annai import pluginhandler, plugins
import aihandler
import config
import frontends

def _get_plugin(ai, plug_name):
    """Get a plugin for this AI (automatically deteremine plugin type)."""
    if isinstance(ai, OneOnOne):
        return pluginhandler.get_oneonone(plug_name)
    elif isinstance(ai, ManyOnMany):
        return pluginhandler.get_manyonmany(plug_name)
    else:
        raise TypeError, "First argument must be an AI instance."

def _mod_plugins(ai, party, message):
    """Checks if the message wants to modify plugin settings.
    
    @param message: Message to check.
    @type message: C{unicode}
    @param ai: Instance of the Artificial Intelligence class handling this
        message.
    @type ai: L{OneOnOne} or L{ManyOnMany} instance
    @param party: Frontend instance associated with given ai instance.
    @type party: L{frontends.BaseIndividual} or L{frontends.BaseGroup}
    @return: Message to deliver to the sender or None if the sender doesn't
        want to do anything about the plugins.
    @rtype: C{unicode} or C{None}

    """
    if __debug__:
        if not (isinstance(ai, OneOnOne) or isinstance(ai, ManyOnMany)):
            raise TypeError, "First argument must be an AI instance."
        if not (isinstance(party, frontends.BaseIndividual)
                or isinstance(party, frontends.BaseGroup)):
            raise TypeError, "Second argument must be a frontend party."
    if message.startswith("load plugin "):
        cmd_str = message[len("load plugin "):].split()
        plug_name = cmd_str[0]
        try:
            plug_cls = _get_plugin(ai, plug_name)
        except pluginhandler.NoSuchPluginError, e:
            return unicode(e)
        try:
            ai.plugins.append(plug_cls(party, cmd_str[1:]))
            return u"k."
        except plugins.PluginError, e:
            return unicode(e)

    if message.startswith("unload plugin "):
        plug_name = message[len("unload plugin "):]
        try:
            plug_cls = _get_plugin(ai, plug_name)
        except pluginhandler.NoSuchPluginError, e:
            return unicode(e)
        for plugin in ai.plugins:
            if plugin.__class__ is plug_cls:
                ai.plugins.remove(plugin)
                return u"k."
        return u"This plugin was not loaded."

    if message.lower() == "list loaded plugins":
        if ai.plugins:
            plug_names = u"\n- ".join((unicode(p) for p in ai.plugins))
            return u"plugins:\n- %s" % plug_names
        else:
            return u"no plugins loaded"

    if message.lower() == "list available plugins":
        return u",\n".join(pluginhandler.get_names())

    if message.lower().startswith("about plugin "):
        name = message[len("about plugin "):]
        try:
            return u"About %s: %s" % (name, pluginhandler.about(name))
        except pluginhandler.NoSuchPluginError, e:
            return unicode(e)

    # If it had nothing to do with moderating plugins, return None.
    return None

class OneOnOne(ai.BaseOneOnOne):
    def __init__(self, identity):
        if __debug__:
            if not isinstance(identity, frontends.BaseIndividual):
                raise TypeError, "Identity must be an Individual."
        self.conf = config.get_conf_copy()
        self.ident = identity
        self.plugins = []

    def handle(self, message):
        """Call all plugins and send back an answer if appropriate."""
        if __debug__:
            if not isinstance(message, unicode):
                raise TypeError, "Message must be a unicode object."
        # Replace some stuff in the reply:
        replacedict = dict(
                user=self.ident.get_name(),
                nick=self.conf.misc["bot_nickname"]
                )
        reply = self.general_reply(message)
        for plugin in self.plugins:
            try:
                message, reply = plugin.process(message, reply)
            except plugins.PluginError, e:
                self.ident.send(unicode(e))
                self.plugins.remove(plugin)

        if reply is not None:
            self.ident.send(custom_replace(reply, **replacedict))

    def general_reply(self, message):
        """Tries to come up with a reply to this message without plugins.

        If no reply is found None is returned. Otherwise a unicode object is
        returned.

        """
        if __debug__:
            if not isinstance(message, unicode):
                raise TypeError, "Message must be a unicode object."
        identity = self.ident
        reply = None
        message = message.strip()

        if message.startswith("load module "):
            ai_str = message[len("load module "):]
            try:
                self.ident.set_AI(aihandler.get_oneonone(ai_str)(self.ident))
                return u"Success!"
            except aihandler.NoSuchAIError, e:
                return unicode(e)

        return _mod_plugins(self, self.ident, message)

class ManyOnMany(ai.BaseManyOnMany):
    def __init__(self, room):
        if __debug__:
            if not isinstance(room, frontends.BaseGroup):
                raise TypeError, "Identity must be an Individual."
        self.conf = config.get_conf_copy()
        self.plugins = []
        self.room = room

    def handle(self, message, sender):
        """Process incoming groupmessage.

        @TODO: Don't send > 2 newlines unless explicitly allowed to.

        """
        if __debug__:
            if not isinstance(sender, frontends.BaseGroupMember):
                raise TypeError, "Sender must be a GroupMember."
            if not isinstance(message, unicode):
                raise TypeError, "Message must be a unicode object."
        message = message.strip()
        reply = None

        mynick = self.room.get_mynick().lower()
        if message.lower().startswith(mynick):
            highlight = message[len(mynick):]
            for elem in self.conf.misc["highlight"]:
                # Check if we have nickanme + one hlchar.
                if highlight.startswith(elem):
                    msg = highlight[len(elem):].strip()
                    return self.highlight(msg, sender)

        for plugin in self.plugins:
            try:
                message, reply = plugin.process(message, reply, sender)
            except plugins.PluginError, e:
                self.room.send(unicode(e))
                self.plugins.remove(plugin)

        if reply is not None:
            reply = custom_replace(reply, user=sender.nick, nick=mynick)
            self.room.send(reply)
        return

    def highlight(self, message, sender):
        """This is for when highlighted in a groupchat.

        @param message: The received message (without highlight-prefix).
        @type message: C{unicode}
        @param sender: The group member that sent the message.
        @type sender: L{frontends.BaseGroupMember}

        """
        if __debug__:
            if not isinstance(message, unicode):
                raise TypeError, "Message must be unicode."
            if not isinstance(sender, frontends.BaseGroupMember):
                raise TypeError, "Sender must be a GroupMember."
        reply = None
        # Replace dictionary.
        replace = dict(
                user=sender.nick,
                nick=self.room.get_mynick(),
                )

        leave_rex = re.compile(u"((please )?leave)|(exit)",
                                        re.IGNORECASE | re.UNICODE)
        if leave_rex.search(message) is not None:
            self.room.send(u"... :'(")
            self.room.leave()
            return
        elif message.startswith("change your nickname to "):
            self.room.set_mynick(message[len("change your nickname to "):])
        elif message.startswith("load module "):
            ai_name = message[len("load module "):]
            try:
                self.room.set_AI(aihandler.get_manyonmany(ai_name)(self.room))
                reply = u"success!"
            except aihandler.NoSuchAIError, e:
                reply = unicode(e)
        else:
            reply = _mod_plugins(self, self.room, message)

        for plugin in self.plugins:
            try:
                message, reply = plugin.process(message, reply, sender)
            except plugins.PluginError, e:
                self.room.send(unicode(e))
                self.plugins.remove(plugin)

        if reply:
            # Pick a random highlighting char:
            hlchar = random.choice(self.conf.misc["highlight"])
            reply = u"%s%s %s" % (sender.nick, hlchar, reply)
            self.room.send(reply)

def custom_replace(message, **replace):
    """This function replaces the message with elements from the dict.

    If an error occurs (eg.: due to wrong formatting of the message) it is
    catched and an appropriate message is returned.

    """
    try:
        return message % replace
    except KeyError, e:
        return ''.join(('I was told to say "%s" now but I don\'t know what to',
                        ' replace %%(%s)s with.')) % (message, e[0])
    except StandardError, e:
        return ''.join(('I was taught to say "%s" now, but there seems to be'
                        ' something wrong with that..')) % message
