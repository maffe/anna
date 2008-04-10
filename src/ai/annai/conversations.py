"""The conversation classes for the annai AI module."""

import random
import re
try:
    import threading as _threading
except ImportError:
    import dummy_threading as _threading

import ai
from ai.annai import pluginhandler, plugins
import aihandler
import config
import frontends

#: The first time an AI instance is created, import all plugins.
_plugins_import_lock = _threading.Lock()

def _get_plugin(ai, plug_name):
    """Get a plugin for this AI (automatically deteremine plugin type)."""
    if isinstance(ai, OneOnOne):
        return pluginhandler.get_oneonone(plug_name)
    elif isinstance(ai, ManyOnMany):
        return pluginhandler.get_manyonmany(plug_name)
    else:
        raise TypeError, "First argument must be an AI instance."

def _del_numeric_plugin(ai, num):
    """Delete a plugin with this number from this ai instance."""
    try:
        del ai.plugins[num]
        return u"k."
    except IndexError:
        return u"No plugin with that number."

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

    # Load one plugin.
    if message.startswith("load plugin "):
        argv = message[len("load plugin "):].split()
        try:
            plug_cls = _get_plugin(ai, argv[0])
            ai.plugins.append(plug_cls(party, argv[1:]))
            return u"k."
        except (pluginhandler.NoSuchPluginError, plugins.PluginError), e:
            return unicode(e)

    # Load multiple plugins at once.
    elif message.startswith("load plugins "):
        for argv_str in re.split(", ?", message[len("load plugins "):]):
            argv = argv_str.split()
            try:
                plug_cls = _get_plugin(ai, argv[0])
                ai.plugins.append(plug_cls(party, argv[1:]))
            except (pluginhandler.NoSuchPluginError, plugins.PluginError), e:
                msg = u"Stopped at plugin %s. Error: %s" % (argv[0], e)
                return msg
        return u"k."

    # Unload a plugin.
    elif message.startswith("unload plugin "):
        plug_name = message[len("unload plugin "):]
        try:
            return _del_numeric_plugin(ai, int(plug_name) - 1)
        except ValueError:
            try:
                plug_cls = _get_plugin(ai, plug_name)
            except pluginhandler.NoSuchPluginError, e:
                return unicode(e)
        valid_req = False
        # Copy of the old plugin list without instances of given class.
        filtered = []
        for plugin in ai.plugins:
            if plugin.__class__ is plug_cls:
                plugin.unloaded()
            else:
                filtered.append(plugin)
        if len(filtered) == len(ai.plugins):
            return u"This plugin was not loaded."
        else:
            ai.plugins = filtered
            return u"k"

    # List loaded.
    elif message.lower() == "list loaded plugins":
        if ai.plugins:
            msg = [u"Loaded plugins:"]
            for num, plugin in enumerate(ai.plugins):
                msg.append(u"%d: %s" % (num + 1, plugin))
            return u"\n".join(msg)
        else:
            return u"no plugins loaded"

    # List available.
    elif message.lower() == "list available plugins":
        return "Available:\n- " + u"\n- ".join(pluginhandler.get_names())

    # About plugin.
    elif message.lower().startswith("about plugin "):
        name = message[len("about plugin "):]
        try:
            return u"About %s: %s" % (name, pluginhandler.about(name))
        except pluginhandler.NoSuchPluginError, e:
            return unicode(e)

    # List command fallback.
    elif message.lower() == "list plugins":
        return u"Loaded or available plugins?"

    # It had nothing to do with moderating plugins.
    return None

class _AnnaiBase(object):
    """Base class for all annai AI classes.

    Takes care of importing all needed plugins the first time an AI class is
    instantiated so make sure to call L{__init__} from child-classes too!

    """
    def __init__(self):
        global _plugins_import_lock
        if _plugins_import_lock.acquire(False):
            pluginhandler.start()
        self.conf = config.get_conf_copy()
        self.plugins = []

    def _flush_plugins(self):
        """Cleans up all loaded plugins."""
        for plugin in self.plugins[:]:
            self.plugins.remove(plugin)
            plugin.unloaded()

class OneOnOne(_AnnaiBase, ai.BaseOneOnOne):
    def __init__(self, identity):
        _AnnaiBase.__init__(self)
        if __debug__:
            if not isinstance(identity, frontends.BaseIndividual):
                raise TypeError, "Identity must be an Individual."
        self.ident = identity

    def _general_reply(self, message):
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
            except aihandler.NoSuchAIError, e:
                return unicode(e)
            else:
                self._flush_plugins()
                return u"Success!"

        return _mod_plugins(self, self.ident, message)

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
        reply = self._general_reply(message)
        for plugin in self.plugins[:]:
            try:
                message, reply = plugin.process(message, reply)
            except plugins.PluginError, e:
                self.ident.send(unicode(e))
                self.plugins.remove(plugin)
                plugin.unloaded()

        if reply is not None:
            self.ident.send(custom_replace(reply, **replacedict))

class ManyOnMany(_AnnaiBase, ai.BaseManyOnMany):
    _rex_nickchange = re.compile(u"change (?:y(?:our|a) )?(?:nick(?:name)?|name) to (.+)$")

    def __init__(self, room):
        _AnnaiBase.__init__(self)
        if __debug__:
            if not isinstance(room, frontends.BaseGroup):
                raise TypeError, "Identity must be an Individual."
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

        for plugin in self.plugins[:]:
            try:
                message, reply = plugin.process(message, reply, sender, False)
            except plugins.PluginError, e:
                self.room.send(unicode(e))
                self.plugins.remove(plugin)
                plugin.unloaded()

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

        res = self._rex_nickchange.match(message)
        if res is not None:
            self.room.set_mynick(res.group(1))
            reply = u"k."
        elif re.match(u"((please )?leave)|(exit)$", message, re.I) is not None:
            self.room.send(u"... :'(")
            self.room.leave()
            return
        elif message.startswith("load module "):
            ai_name = message[len("load module "):]
            try:
                self.room.set_AI(aihandler.get_manyonmany(ai_name)(self.room))
            except aihandler.NoSuchAIError, e:
                reply = unicode(e)
            else:
                self._flush_plugins()
                reply = u"success!"
        else:
            reply = _mod_plugins(self, self.room, message)

        for plugin in self.plugins[:]:
            try:
                message, reply = plugin.process(message, reply, sender, True)
            except plugins.PluginError, e:
                self.room.send(unicode(e))
                self.plugins.remove(plugin)
                plugin.unloaded()

        if reply:
            # As IRC-customs dictate (yucky, frontend-dependent hacks): "/me "
            # is a special action-prefix and should not be spoiled by
            # highlighting.
            if not reply.startswith("/me "):
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
        # Keep original %'s in message intact.
        return message.replace("%", "%%") % replace
    except KeyError, e:
        return ''.join(('I was told to say "%s" now but I don\'t know what to',
                        ' replace %%(%s)s with.')) % (message, e[0])
    except StandardError, e:
        return ''.join(('I was taught to say "%s" now, but there seems to be'
                        ' something wrong with that..')) % message
