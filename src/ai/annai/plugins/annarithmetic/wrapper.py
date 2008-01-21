"""Plugin that performs arithmetic operations if input is appropriate.

Automatically detects messages that are equations and solves them. Acts
'shy'; if another plugin already came up with a reply before this plugin
did, it does not even try to parse the incoming message.

@TODO: Check thread-safety.
@TODO: Load JVM with correct classpath just once.

"""
import jpype as j
import os

from ai.annai.plugins import BasePlugin

class _Plugin(BasePlugin):
    def __init__(self, party, args):
        self.party = party
        assert(j.isJVMStarted())
        j.attachThreadToJVM()
        self.jplugin = j.JPackage("annarithmetic").Plugin()
        j.detachThreadFromJVM()

    def __unicode__(self):
        return u"Annarithmetic plugin."

    def process(self, message, reply, sender=None):
        """@TODO: The java plugin should return an empty string on no-match."""
        if reply is not None:
            return (message, reply)
        j.attachThreadToJVM()
        if message == "annarithmetic usage":
            result = self.jplugin.usage()
        else:
            result = self.jplugin.parseString(str(message))
        assert(isinstance(result, unicode))
        # HACK: plugin returns message on no-match.
        #if not result:
        if result == message:
            result = reply
        j.detachThreadFromJVM()
        return (message, result)

class OneOnOnePlugin(_Plugin):
    pass

class ManyOnManyPlugin(_Plugin):
    pass

if not j.isJVMStarted():
    relative = os.path.join("ai", "annai", "plugins", "annarithmetic")
    full = os.path.join(os.path.abspath(os.curdir), relative)
    cp = os.path.join("-Djava.class.path=%s" % full, "annarithmetic.jar")
    j.startJVM(j.getDefaultJVMPath(), cp)
