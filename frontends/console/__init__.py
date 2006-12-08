'''The console frontend. This allows the user to communicate with the
bot interactively through a console session on the same box as the chatbot
itself.'''

import sys

__all__ = ["connection"]

class PM:

	def __init__( self, nickname = "you" ):
		self.nickname = nickname

	def __str__( self ):
		return "console-user"

	def getAI( self ):
		return self.ai
	
	def getNick( self ):
		return self.nickname
	
	def getUid( self ):
		return 1

	def setAI( self, aiModule ):
		self.ai = aiModule
	
	def setNick( self, nick ):
		self.nickname = nick
	
	def isAllowedTo( self, what ):
		return True

	def send( self, message ):
		if message[:4] == "/me ":
			sys.stdout.write( "* anna " + message[4:].encode( "utf8" ) + "\n" )
		else:
			sys.stdout.write( "<anna> " + message.encode( "utf8" ) + "\n" )
