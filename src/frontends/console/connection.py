"""This is the console frontend to the Anna bot.

It allows the user to communicate with the bot directly through stdin
and stdout but lacks certain functionality for obvious reasons (such as
group-chat support).

"""
import getpass
import os
try:
    import threading as _threading
except ImportError:
    import dummy_threading as _threading

import aihandler
import communication as c
import config
from frontends import BaseConnection
from frontends.console.parties import Individual

USAGE = u"""\
Welcome to the interactive Anna shell.  Just type a message as you
normally would.

WARNING: this frontend blocks the stdout on every prompt. To prevent the
output buffer from growing too big, it should only be used alone or at
least not left without input for long periods of time while other
frontends produce lots of output.

"""

class Connection(BaseConnection, _threading.Thread):
    def __init__(self):
        _threading.Thread.__init__(self, name="console frontend")
        self.idnty = Individual(getpass.getuser())
        self.def_AI = config.get_conf_copy().misc["default_ai"]

    def connect(self):
        # The connection will be closed when this is set to True.
        self.halt = False
        # Exit when this is the only thread left (in particular: when the main
        # thread has exited).
        self.setDaemon(True)
        self.start()

    def disconnect(self):
        self.halt = True

    def run(self):
        """Take over the stdin and do nifty stuff... etc.

        This method is called as a seperate thread from the main script so it
        must be thread-safe.

        """
        c.stdout_block(USAGE)
        self.idnty.set_AI(aihandler.get_oneonone(self.def_AI)(self.idnty))
        try:
            while not self.halt:
                # The AI can change at run-time.
                ai = self.idnty.get_AI()
                ai.handle(c.stdin(u"<%s> " % self.idnty))
        except EOFError:
            c.stdout_block(u"\n")
