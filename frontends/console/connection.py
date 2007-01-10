'''connects the chatbot to the stdin and stdout'''

import sys
import os
import pwd #password database, for uid <--> username lookup

import frontends.console as console_frontend
import aihandler
import admin

username = pwd.getpwuid( os.getuid() )[0]
identity = console_frontend.PM( username )

def connect():
	'''take over the stdin and do nifty stuff... etc.'''

	print "Welcome to the interactive Anna shell. just type a message as you normally would."
	print "To quit, hit ctrl + d."

	try:
	 while( True ):

		sys.stdout.write( "<%s> " % identity )

		message = sys.stdin.readline()
		if not message: #EOF
			print #print a newline to prevent outputting on the input line
			admin.stop()

		ai = aihandler.getAIReferenceByAID( "chat_english" )
		ai.direct( message, identity, "console" )

	except KeyboardInterrupt:
		print
		admin.stop()
