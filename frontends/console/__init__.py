# vim:fileencoding=utf-8

"""
The console frontend. This allows the user to communicate with the bot
interactively through a console session on the same box as the chatbot itself.
"""

import sys

import aihandler
import config
import pluginhandler

__all__ = ["connection"]

class PM:

	def __init__(self, nickname = "you"):
		self.nickname = nickname

	def __str__(self):
		return self.nickname

	def getAI(self):
		return aihandler.getAIReferenceByUID(0)

	def getNick(self):
		return self.nickname

	def getPlugins(self):
		"""Return an iterable with all plugins assigned to this identity.

		Note that loading the default plugins is the responsibility of the AI
		module, not the frontend. If no plugins were previously loaded, a
		ValueError is raised.
		
		"""
		#The pluginhandler raises the ValueError exception.
		return pluginhandler.getPlugins(0)

	def getType(self):
		return "console"

	def getUid(self):
		return 0

	def setAI(self, aiModule):
		return aihandler.setAID(0, aiModule.ID)

	def setNick(self, nick):
		self.nickname = nick

	def isAllowedTo(self, what):
		return True

	def send(self, message):

		botName = config.misc['bot_nickname']
		if message.startswith("/me "):
			output = "* %s %s\n" % (botName, message[4:].encode("utf-8"))
		else:
			output = "<%s> %s\n" % (botName, message.encode("utf-8"))

		sys.stdout.write(output)

class MUC:
	"""Bogus class. Simply here to meet API requirements."""

	def __init__(self, id, nick = None, mood = 0, behaviour = ''):
		pass

	def __str__(self):
		return ""

	def changeNick(self, new):
		return

	def join(self, force = False):
		return

	def leave(self, force = False):
		return

	def send(self, message):
		return

	def addParticipant(self, participant, force = False):
		return

	def delParticipant(self, nick):
		return

	def getBehaviour(self):
		return 0

	def getJid(self, asstring):
		return ""

	def getMood(self):
		return 0

	def getNick(self):
		return ""

	def getParticipant(self, nick):
		return MUCParticipant()

	def getParticipants(self):
		return ()
	
	def getPlugins(self):
		return ()

	def getType(self):
		return "console"

	def getUid(self):
		return 0

	def isActive(self):
		return False

	def isParticipant(self, nick):
		return False

	def setActive(self):
		return

	def setBehaviour(self, behaviour):
		return
	
	def setNick(self, nick):
		return

	def setInActive(self):
		return
