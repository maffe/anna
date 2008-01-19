"""This is the console frontend to the Anna bot.

It allows the user to communicate with the bot directly through stdin
and stdout but lacks certain functionality for obvious reasons (such as
group-chat support).



"""
import os
import pwd #password database, for system uid <--> username lookup
import sys
try:
    import threading as _threading
except ImportError:
    import dummy_threading as _threading
import time
import types

import aihandler
import communication as c
import config
from frontends import BaseConnection
from frontends.console.parties import Individual

USAGE = u"""Welcome to the interactive Anna shell.  Just type a message
as you normally would.   First, you need to specify which AI module you
would like to use.  To quit this frontend (not the bot), hit ctrl + D.

WARNING: this frontend blocks the stdout on every prompt. To prevent the
output buffer from growing too big, it should only be used alone or at
least not left without input for long periods of time while other
frontends produce lots of output.

"""
CHOOSE_AI = u"""Please choose an ai to load from the following list:
%s
>>> """

class Connection(BaseConnection, _threading.Thread):
    def __init__(self):
        _threading.Thread.__init__(self, name="console frontend")
        username = pwd.getpwuid(os.getuid())[0]
        self.idnty = Individual(username)

    def connect(self):
        # The connection will be closed when this is set to True.
        self.halt = False
        self.start()

    def disconnect(self):
        self.halt = True

    def get_ai(self):
        """Ask the user what AI module to use and return its reference."""
        def_ai = config.get_conf_copy().misc["default_ai"]
        while 1:
            ais = []
            for name in aihandler.get_names():
                if name.lower() == def_ai.lower():
                    name = u" ".join((name, "(default)"))
                ais.append(u"- %s\n" % name)
            # This can raise an EOFError.
            choice = c.stdin(CHOOSE_AI % u"".join(ais)).strip()
            if choice == "":
                choice = def_ai
            elif choice.endswith(" (default)"):
                # If the user thought " (default)" was part of the name, strip.
                choice = choice[:-len(" (default)")]
            try:
                self.idnty.set_AI(aihandler.get_oneonone(choice)(self.idnty))
                break
            except aihandler.NoSuchAIError, e:
                c.stderr_block(unicode(e))
                c.stdout_block(u"Please try again.\n")
        c.stdout_block(u'Module "%s" successfully loaded.\n' % choice)

    def run(self):
        """Take over the stdin and do nifty stuff... etc.

        This method is called as a seperate thread from the main script so it
        must be thread-safe.

        """
        c.stdout_block(USAGE)
        try:
            self.get_ai()
            while not self.halt:
                # The AI can change at run-time.
                ai = self.idnty.get_AI()
                ai.handle(c.stdin(u"<%s> " % self.idnty))
        except EOFError:
            c.stdout_block(u"\n")
