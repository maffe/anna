# encoding: utf-8

'''The console frontend. This allows the user to communicate with the
bot interactively through a console session on the same box as the chatbot
itself.'''

import sys

import config

__all__ = ["connection"]

class PM:

	def __init__( self, nickname = "you" ):
		self.nickname = nickname

	def __str__( self ):
		return self.nickname

	def getAI( self ):
		return self.ai
	
	def getNick( self ):
		return self.nickname
	
	def getUid( self ):
		return 0

	def setAI( self, aiModule ):
		self.ai = aiModule
	
	def setNick( self, nick ):
		self.nickname = nick
	
	def isAllowedTo( self, what ):
		return True

	def send( self, message ):

		botName = config.misc['bot_nickname']
		if message[:4] == "/me ":
			output = "* %s %s\n" % (botName, message[4:].encode( "utf-8" ))
		else:
			output = "<%s> %s\n" % (botName, message.encode( "utf-8" ))

		sys.stdout.write( output )

class MUC:
	'''Bogus class. Simply here to meet API requirements.'''

	def __init__( self, id, nick = None, mood = 0, behaviour = '' ):
		pass

	def __str__( self ):
		return ""

	def changeNick( self, new ):
		return

	def join( self, force = False ):
		return

	def leave( self, force = False ):
		return

	def send( self, message ):
		return

	def addParticipant( self, participant, force = False ):
		return

	def delParticipant( self, nick ):
		return

	def getBehaviour( self ):
		return 0

	def getJid( self, asstring ):
		return ""

	def getMood( self ):
		return 0

	def getNick( self ):
		return ""

	def getParticipant( self, nick ):
		return MUCParticipant()

	def getParticipants( self ):
		return ()

	def getType( self ):
		return "console"

	def getUid( self ):
		return 0

	def isActive( self ):
		return False

	def isParticipant( self, nick ):
		return False

	def setActive( self ):
		return

	def setBehaviour( self, behaviour ):
		return
	
	def setNick( self, nick ):
		return

	def setInActive( self ):
		return
