'''connects the chatbot to the stdin and stdout'''

import sys
import os
import pwd #password database, for uid <--> username lookup
import threading

import frontends.console as console_frontend
import aihandler

class ConnectThread( threading.Thread ):

	def __init__( self ):
		threading.Thread.__init__( self )
	
	def run( self ):
		'''take over the stdin and do nifty stuff... etc.'''

		print "Welcome to the interactive Anna shell. just type a message as you normally would."

		while( True ):
			username = pwd.getpwuid( os.getuid() )[0]
			identity = console_frontend.PM( username )
			sys.stdout.write( "<" + identity.getNick() + "> " )
			message = sys.stdin.readline()
			ai = aihandler.getAIReferenceByAID( "chat_english" );
			ai.direct( message, identity, "console" )
