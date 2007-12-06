"""This is the console frontend to the Anna bot.

It allows the user to communicate with the bot directly through stdin and
stdout but lacks certain functionality for obvious reasons (such as group-chat
support).

"""
import os
import pwd #password database, for system uid <--> username lookup
import sys
import types

import aihandler
import config
from frontends import BaseConnection
from frontends.console.parties import Individual

USAGE = """
Welcome to the interactive Anna shell.  Just type a message as you
normally would.  First, you need to specify which AI module you would
like to use.  To quit, hit ctrl + d or ctrl + c.
"""

class Connection(BaseConnection):
    def __init__(self):
        username = pwd.getpwuid(os.getuid())[0]
        self.idnty = Individual(username)

    def get_ai(self):
        """Ask the user what AI module to use and return its reference.
        
        If the supplied value is not a correct AID (AI identifier) the default
        module is returned.  There is only one chance; no "please try again".
        
        """
        def_ai = config.get_conf_copy().misc["default_ai"]
        while 1:
            print "Please choose which ai you want to load from the following list:"
            for name in aihandler.get_names():
                print " -", name,
                if name.lower() == def_ai.lower():
                    print "(default)"
                else:
                    print
            # This can raise an EOFError.
            choice = raw_input(">>> ").strip()
            if choice == "":
                choice = def_ai
            try:
                self.idnty.set_AI(aihandler.get_oneonone(choice)(self.idnty))
                break
            except ValueError, e:
                print >> sys.stderr, e
                print "Please try again.\n"
        print 'Module "%s" successfully loaded.' % choice

    def connect(self):
        """Take over the stdin and do nifty stuff... etc.

        This method is called as a seperate thread from the main script so it
        must be thread-safe.

        """
        print USAGE
        try:
            self.get_ai()
            while 1:
                message = raw_input("<%s> " % self.idnty)
                ai = self.idnty.get_AI()
                ai.handle(message.decode(sys.stdin.encoding))
        except KeyboardInterrupt:
            print
            return
        except EOFError:
            print
            return
