###############################################################################
"""This is the console frontend to the Anna bot.

It allows the user to communicate with the bot directly through stdin and
stdout but lacks certain functionality for obvious reasons (such as group-chat
support).

"""
import os
import pwd #password database, for uid <--> username lookup
import sys
import types

import admin
import aihandler
import frontends.console as console_frontend

usage = """
Welcome to the interactive Anna shell. Just type a message as you normally
would. First, you need to specify which AI module you would like to use. To
quit, hit ctrl + d or ctrl + c.
"""

username = pwd.getpwuid(os.getuid())[0]
identity = console_frontend.PM(username)

def connect():
	"""Take over the stdin and do nifty stuff... etc."""
	print usage
	identity.setAI(chooseAI())
	try:
		while True:
			sys.stdout.write("<%s> " % identity)
			message = sys.stdin.readline()
			if not message: #EOF
				print # Print a newline to prevent outputting on the input line.
				admin.stop()
			ai = identity.getAI()
			ai.direct(message[:-1], identity)
			# Leave out the appending newline.
	except KeyboardInterrupt:
		print
		admin.stop()

def chooseAI():
	"""Ask the user what AI module to use and return its reference.
	
	If the supplied value is not a correct AID (AI identifier) the default module
	is returned. This is hard-coded to be "annai", which is pretty ugly, but ok.
	It's a TODO :). There is only one chance; no "please try again".
	
	"""
	print "Please choose which ai you want to load from the following list:\n-", \
		"\n- ".join([x.ID for x in aihandler.getAll()])
	print 'By default the "annai" module is selected.'
	sys.stdout.write(">>> ")
	choice = sys.stdin.readline().strip()
	ai = aihandler.getAIReferenceByAID(choice)
	if isinstance(ai, types.IntType):
		print 'You did not supply a valid AI name. Default module ("annai") loaded.'
		return aihandler.getAIReferenceByAID("annai")
	else:
		print 'Module "%s" successfully loaded.' % choice
		return ai
