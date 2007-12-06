"""This is the console frontend to the Anna bot.

It allows the user to communicate with the bot directly through stdin and
stdout but lacks certain functionality for obvious reasons (such as group-chat
support).

"""
import os
import pwd #password database, for system uid <--> username lookup
import sys
import types

import admin
import aihandler
from frontends import BaseConnection
from frontends.console.parties import *

USAGE = """
Welcome to the interactive Anna shell. Just type a message as you normally
would. First, you need to specify which AI module you would like to use. To
quit, hit ctrl + d or ctrl + c.
"""

class Connection(BaseConnection):
    def __init__(self):
        username = pwd.getpwuid(os.getuid())[0]
        self.identity = Individual(username)

    def get_ai(self):
        """Ask the user what AI module to use and return its reference.
        
        If the supplied value is not a correct AID (AI identifier) the default
        module is returned. This is hard-coded to be "annai", which is pretty ugly,
        but OK.  It's a TODO :). There is only one chance; no "please try again".
        
        """
        print "Please choose which ai you want to load from the following list:"
        for ai in aihandler.getAll():
            print " -", ai.ID
        print 'By default the "annai" module is selected.'
        sys.stdout.write(">>> ")
        choice = sys.stdin.readline().strip()
        self.ai = aihandler.getAIReferenceByAID(choice)
        if isinstance(self.ai, int):
            print "You did not supply a valid AI name. Default module loaded."
            self.ai = aihandler.getAIReferenceByAID("annai")
        else:
            print 'Module "%s" successfully loaded.' % choice

    def connect(self):
        """Take over the stdin and do nifty stuff... etc.
        
        This method is called as a seperate thread from the main script so it
        must be thread-safe.
        
        """
        print USAGE
        self.get_ai()
        id = self.identity
        id.set_AI(self.ai)
        try:
            while 1:
                sys.stdout.write("<%s> " % id)
                message = sys.stdin.readline()
                if not message: #EOF
                    print
                    admin.stop()
                ai = self.identity.getAI()
                ai.direct(message[:-1], self.id)
        except KeyboardInterrupt:
            print
            admin.stop()
