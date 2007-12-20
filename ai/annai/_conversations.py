"""The 'official' AI module for Anna (english)."""

import random
import re

import ai
import config

# Pre-compiled regular expressions.
_REX_PM_LEAVE_MUC = re.compile("((please )?leave)|(exit)", re.IGNORECASE)

class OneOnOne(ai.BaseOneOnOne):
    def __init__(self, identity):
        self.ident = identity
        self.conf = config.get_conf_copy()

    def handle(self, message):
        """Call all plugins and send back an answer if appropriate."""
        reply = self.general_reply(message)
        try:
            plugins = self.ident.get_plugins()
        except ValueError:
            plugins = pluginhandler.get_default_PM()
            self.ident.set_plugins(plugins)
        for plugin in plugins:
            message, reply = plugin.process(self.ident, message, reply)

        if reply is not None:
            self.ident.send(reply)

    def general_reply(self, message):
        """Tries to come up with a reply to this message without plugins.

        If no reply is found None is returned. Otherwise a unicode object is
        returned. The message argument must also be a unicode object.

        """
        assert(isinstance(message, unicode))
        identity = self.ident
        reply = None
        message = message.strip()

        # Replace some stuff in the reply:
        replacedict = dict(
                user=self.ident.get_name(),
                nick=self.conf.misc["bot_nickname"]
                )
        if message.startswith(u"load module "):
            ai_str = message[12:]
            try:
                ai_class = aihandler.get_oneonone(ai_str)
                new_ai = ai_class(self.ident)
                self.ident.set_AI(new_ai)
                return u"Success!"
            except ValueError, e:
                return u"Failed to load module %s: %s" % (ai_str, e)

        # HandlePlugins() Does not actually apply plugins; just checks commands
        # to moderate them.
        return self.handle_plugins(message)

    def handlePlugins(self, message):
        """Checks if the message wants to modify plugin settings and applies
        them to given identity."""

        uid = identity.getUid()

        if message.startswith("load plugin "):
            try:
                pluginhandler.addPlugin(uid, message[12:])
                return "k."
            except ValueError:
                return "plugin not found."
        
        if message.startswith("unload plugin "):
            try:
                pluginhandler.removePlugin(uid, message[14:])
                return "k."
            except ValueError:
                return "plugin not found."

        if message.lower() == "list plugins":
            try:
                plugins = pluginhandler.getPlugins(uid)
                return "plugins:\n- " + "\n- ".join([plugin.ID for plugin in plugins])
            except ValueError:
                return "no plugins loaded"

        if message.lower() == "list available plugins":
            #TODO: nice textual representation of this iterable element
            return str(pluginhandler.getAllPlugins())

        #if it wasn't anything, return None.
        return None

def room(message, sender, room):
    """Use this function to get yourself a reply that fits a mutli user
    chat message.

    - If the message starts with the current nickname followed by a
      highlighting character, handle it with mucHighlight().
    - Call all loaded modules.
    - If any of the above gave a result by setting the "message" variable,
      send that very variable back to the room with muc.send().
        
    """
    typ = room.getType()
    nickname = room.getNick()
    replace = {
        'user': sender.getNick(),
        'nick': room.getNick(),
    }

    if sender.getNick().lower() == nickname.lower():
        return False  #prevent loops
    message = filters.xstrip(message)
    reply = None

    # Handle messages with leading nick as direct messages.
    for elem in config.Misc.hlchars:
        # Check if we have nickanme + one hlchar.
        if message.startswith(''.join((nickname, elem))):
            return mucHighlight(message, sender, room)

    # Apply plugins.
    try:
        plugins = room.getPlugins()
    except ValueError:
        plugins = pluginhandler.getDefaultMUC()
        room.setPlugins(plugins)
    for plugin in plugins:
        message, reply = plugin.process(room, message, reply)

    if reply and room.getBehaviour() != 0:
        if (reply.count('\n') > 2 or len(reply) > 255) and room.getBehaviour() < 3:
            room.send(''.join(("Sorry, if I would react to that it would spam the",
                               " room too much. Please repeat it to me in PM.")))
        else:
            reply = mucReplaceString(reply, replace)
            room.send(reply)


def mucHighlight(message, sender, room):
    """This is for when highlighted in a groupchat."""

    reply = None
    uid = room.getUid()
    nick = room.getNick()
    #TODO: we just 'assume' the highlight character to be of length 1 here
    hlchar = message[len(nick)]
    # Strip the leading nickname and hlcharacter off.
    message = message[(len(nick) + 1):].strip()
    # Replace dictionary.
    replace = {
        'user': sender.getNick(),
        'nick': room.getNick(),
    }

    if re.search(_REX_PM_LEAVE_MUC, message) is not None:
        room.send("... :'(")
        room.leave()
        return

    elif message[:4] == "act ":
        try:
            room.setBehaviour(getBehaviourID(message[4:]))
            reply = "k."
        except ValueError:
            reply = "behaviour not found"

    elif message[:24] == "change your nickname to ":
        room.changeNick(message[24:])

    elif message[:12] == "load module " and message[12:]:
    #the "and message[12:]" prevents trying to load an empty module
        result = aihandler.setAID(uid, message[12:]) #TODO: security?
        if result == 0:
            reply = "success!"
        elif result == 1:
            reply = "no such module"
    elif message == "what's your behaviour?":
        #TODO: this wil crash the bot if room.getBehaviour() returns a false value.
        #bug or feature?
        reply = getBehaviour(room.getBehaviour())

    if not reply:
        reply = handlePlugins(message, room)

    for plugin in sender.getPlugins():
        message, reply = plugin.process(room, message, reply)

    if reply and room.getBehaviour() != 0:

        #pick a random highlighting char:
        #TODO: UGLY UGLY UGLY UGLY UGLY UGLY UGLY!!!!!
        n = random.randint(0, len(config.Misc.hlchars) - 1)
        hlchar = config.Misc.hlchars[n]
        del n
        reply = "%s%s %s" % (sender.getNick(), hlchar, reply)

        #TODO: check if newlines can be inserted in another way
        if (reply.count('\n') > 2 or len(reply) > 255) and room.getBehaviour() < 3:
            room.send("Sorry, if I would react to that it would spam the room too"
                      " much. Please repeat it to me in PM.")
        else:
            room.send(mucReplaceString(reply, replace))


def mucReplaceString(message, replace):
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


def invitedToMuc(room, situation, by = None, reason = None):
    """Handler to call if invited to a muc room.

    Takes:
        - room: the instance of the (unjoined room)
        - situation: the situation we are in and the reason for the invitation.
          situations:
          0) already active in room: return an excuse message to the room
          1) room known, but inactive: join it and say thx 4 inviting
          2) room unknown: create it, join it and say thx
        - by: a unicode containing the name of the person that invited the bot
        - reason: unicode containing the reason for the invite as supplied by
          the inviter
    Technically speaking, the by and reason attributes are valid as long as
    they have a .__str__() method. Of course, unicode should be used throughout
    the entire bot, but it's not necessary.

    """
    #this dictionary holds all the messages that could be sent. it's not very
    #nice because you construct them all even though one is going to be used,
    #but since this is called not very often I thought it would be nice,
    #because it also improves readability. also note that right now the indexes
    #are the situation codes, but that could very well be changed.
    messages = {}
    if reason:
        messages[0] = ''.join(("I was invited to this room, being told '%s',",
                              " but I'm already in here...")) % reason
    else:
        messages[0] = "I was invited to this room again but I'm already in here..."
    #below we also mention who invited to show the admins of the muc.
    messages[1] = "Hey all. Thanks for inviting me again, %s." % by
    messages[2] = "Lo, I'm a chatbot. I was invited here by somebody."

    if situation != 0:
        room.join()

    room.send(messages[situation])


# The different behaviour-levels and their textual representations:
# 1 With this behaviour you should typically not say anything.
# 2 Only talk when talked to.
# 3 React to everything you can react to, even if not addressed.
# 4 Say random things at random moments, be annoying.

behaviour = {
    0: 'silent',
    1: 'shy',
    2: 'normal',
    3: 'loudly'
}

def getBehaviour(id):
    return behaviour[id]

def getBehaviourID(text):
    """Get the numerical ID of the specified behaviour."""
    for elem in behaviour.iteritems():
        if elem[1] == text:
            return elem[0]
    raise ValueError, text

def isBehaviour(arg):
    """Returns True if supplied behaviour (textual OR numerical) is valid."""
    if isinstance(arg, int):
        return arg in behaviour
    else:
        return arg in behaviour.values()
