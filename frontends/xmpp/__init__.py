# vim:fileencoding=utf-8
################################################################################

__all__ = ["connection", "handlers", "rooms"]
import xmpp
import types
import sys

import config
import mysql
import stringfilters as filters
import user_identification as uids

#the connection instance, to be set by the connection module.
conn = None
#personally I believe this instance should be kept by the connection module
#itself, but importing that here causes an import loop. TODO

class PM:
	"""this is a class of a person we're having a one-on-one conversation with."""

	def __init__( self, jid, nick = None ):
		"""Make the instance ready for use by checking if the user was already known
		to us and registering him/her in the database if not. The nick attribute
		allows for a preset nickname to be used. If not specified, the node of the
		jid will be used instead. The jid must be an xmpp.JID() instance."""
		self.jid = jid
		self.nick = nick or jid.getNode()
		self.conn = conn
		self.uid = uids.addUid( jid.getStripped(), 'jabber-pm' )

	def __str__( self ):
		return "xmpp:%s" % self.jid.getStripped()


	def send( self, message ):
		"""Send a personal chat message to jid. takes: message (str)."""
		xml = xmpp.Message( to = self.jid, body = message, typ = "chat" )
		self.conn.send( xml )

	def getAI( self ):
		"""Get the reference to the AI module that is used for this conversation."""
		return self.ai

	def getJid( self ):
		"""Fetch the jid of the user as a xmpp.JID() instance."""
		return self.jid

	def getNick( self ):
		"""Return the nick of the person in a string."""
		return self.nick

	def getType( self ):
		"""Return the type of this identity: 'xmpp'."""
		return "xmpp"

	def getUid( self ):
		"""If you don't understand this one... then..."""
		return self.uid

	def isAllowedTo( self, plok ):
		"""return True if this contact is allowed to do plok (str)"""
		print >> sys.stderr, "DEBUG: using isAllowedTo method from f/x/__init__:PM"
		for elem in self.getPermissions():
			if elem in ( 'all', plok ):
				return True
		else:
			return False

	def setAI( self, aimodule ):
		"""Set an AI module to use for this conversation."""
		self.ai = aimodule



class MUC:
	"""this class will let you create a muc-room object. you can use that object
	to do room-specific tasks, like sending a message, changing the mood of that
	room, get the participants, change the nickname, etcetera.

	self.participants is a dictionary that holds all the members of the room and
	info about them. their nick (unicode string) is used as key and an instance of
	MUCParticipant is used as the content. use the self.getParticipants() functions
	(and other related ones) to access this list rather than accessing it directly.

	note: this doesn't actually join the group chat, it just creates an instance
	of it. to join it, call the join() method.
	
	temp: currently, it's just a dictionary with nicknames as keys and empty values
	(None). this will change soon."""



	def __init__ (
		self,
		jid,
		nick      = config.misc['bot_nickname'],
		mood      = 70,
		behaviour = 2,
	):
		"""declare some variables and join the room.
		takes:
		- jid (xmpp.JID() || unicode): the jid of the room
		- nick (unicode): the preferred nickname of the bot
		- mood (int): the mood-level that goes with this room
		- behaviour (int): our behaviour in this room"""

		jid = xmpp.JID(jid)

		self.mood         = mood
		self.participants = {}
		self.nick         = nick
		self.jid          = xmpp.JID( jid )
		self.active       = False #set to True when we are in this room
		self.setBehaviour( behaviour )
		self.participants = []
		self.conn         = conn
		self.uid = uids.addUid(jid.getStripped(),'jabber-muc')


	def __str__( self ):
		"""Return the jid of the room as a string"""
		return "xmpp:%s" % self.jid


	def changeNick( self, new ):
		"""Try to change the nickname into this. This function is conflict-safe;
		it will not change the nickname when there is a conflict (in fact, it
		will never change the nickname at all but wait for the conference server
		to tell the handler to do this - though that is xmpp specific, whereas
		the aforementioned is not.)"""
		if not self.isActive():
			return
		to = xmpp.JID( self.jid )
		to.setResource( new )
		xml = xmpp.Presence( to = to )
		conn.send( xml )
		

	def join( self, force = False ):
		"""Join a muc room. more precisely; send presence to it.

		Takes:
		- force (bool): don't stop if we are already in there

		TODO: Return an integer indicating the exit status."""

		if self.active and not force:
			return False

		#<presence to="jid/nick">
		#<show>online</show>
		#<status>online</status>
		#<x xmlns="http://jabber.org/protocol/muc" />
		#</presence>

		# to : room@conference-server/nickname
		#(jid: node@domain/resource)

		#make a copy of the jid of the room and set the nickname on it
		jid = xmpp.JID( self.jid )
		jid.setResource( self.nick )

		xml = xmpp.Presence( show = "online", status = "online" )
		xml.setTo( str( jid ) )
		#add <x xmlns="http://jabber.org/protocol/muc" />
		xml.addChild( "x", namespace = xmpp.NS_MUC )

		self.conn.send( xml )
		self.active = True


	def leave( self, force = False ):
		"""leave the muc room. returns if the bot isn't in the room
		(ie: if room.isActive() is False) unless force == True.

	returns an integer:
		- 0: all went well
		- 1: the bot wasn't active in this room in the first place"""
		
		if not self.isActive() and not force:
			return 1

		xml = xmpp.Presence( to = self.jid, typ = 'unavailable' )
		self.conn.send( xml )
		self.setInActive()
		return 0



	def send( self, message ):
		"""Send a message to the room. Takes: message (unicode), the message to send."""

		xml = xmpp.Message( to = self.jid, body = message, typ = 'groupchat' )
		self.conn.send( xml )


	def addParticipant( self, participant, force = False ):
		"""Add a participant to the pool of participants. If force==True, don't
		return False if the participant already exists."""
		if not force and participant in self.participants:
			return False
		else:
			self.participants.append( participant )

	def delParticipant( self, nick ):
		"""Delete a user from the list of participants"""
		for elem in self.participants:
			if elem.nick == nick:
				self.participants.remove( elem )
				return #no need to continue.


	def getBehaviour( self ):
		"""Return the behaviour we have in this room as an integer."""
		return self.behaviour

	def getJid( self, asstring = False ):
		"""Return the jid of this room as an xmpp.JID() instance. The asstring
		parameter will be removed soon. Use str( getJid ) if you want a string."""
		if asstring:
			print >> sys.stderr, "WARNING: using deprecated argument 'asstring'."
			return str( self.jid )
		else:
			return self.jid

	def getMood( self ):
		"""Return the mood value of this room"""
		return self.mood

	def getNick( self ):
		"""Return the nick we have in this chatroom"""
		return self.nick

	def getParticipant( self, nick ):
		"""Return the instance of the participant with this nick (unicode). Note;
		this really raises a KeyError exception if there's no such participant"""
		return self.participants[nick]

	def getParticipants( self ):
		"""Return an iterable object with all the participants"""
		return self.participants

	def getType( self ):
		"""Get the type of this room (returns a string 'xmpp') """
		return "xmpp"

	def getUid( self ):
		"""Return the uid (int) of this room."""
		return self.uid


	def isActive( self ):
		"""Return a boolean that indicates whether we are or are not in this room"""
		return self.active

	def isParticipant( self, nick ):
		"""Return True if nick is a participant of the room, False if not"""
		return nick in [str(elem) for elem in self.participants]

	def setActive( self ):
		"""Set the status of the bot in this room to True (bool). NOTE: this does
		not actually /do/ anything, it's just for internal tracking of the activity.
		If you want to actually join/leave, use the respective methods.
		TODO: shouldn't this module be removed?"""
		self.active = True

	def setBehaviour( self, behaviour ):
		"""Set the behaviour of the group to a specified level. Takes and returns
		an integer. On success 0 is returned."""
		self.behaviour = behaviour
		return 0

	def setNick( self, nick ):
		"""Change nickname to nick (unicode)."""
		self.nick = nick

	def setInActive( self ):
		"""Inverse of self.Active()"""
		self.active = False




## end of class MUC ##



#temp: stub for what the MUCParticipant class will look like

class MUCParticipant:
	"""a member of a groupchat. it holds information like wether he/she is an
	admin, what his/her nickname is, etcetera."""

	def __init__(self,nick,role,status,jid=None):
		"""create the values that will be needed later on"""
		self.nick=nick
		self.status=status
		self.role=role
		if jid:
			self.jid=xmpp.JID(jid)

	def __str__(self):
		"""textual representation of the participant. returns his nick"""
		return self.nick

	def getJid(self):
		"""return participant's jid as an xmpp.JID() instance or 0 (int) if not
		available"""
		try:
			return self.jid
		except ValueError:
			return 0

	def getNick(self):
		"""return participant's nickname"""
		return self.nick

	def getRole(self):
		"""return participant's role"""

	def getStatus(self):
		"""return participant's status"""
		return self.status

	def isActive(self):
		"""check if a participant is active. it is not uncommon, though, to expect
		this to be True if the instance is present without checking."""
		if self.status!='unavailable':
			return True
		else:
			return False

	def isAdmin(self):
		"""return True (bool) if participant's role is admin. useful for interoperability
		with other protocols."""
		if self.role == 'moderator':
			return True
		else:
			return False

	def isOnline(self):
		"""alias for self.isActive() """
		return self.isActive()

	def setNick(self,nick):
		"""set the nickname"""
		self.nick=nick

	def setRole(self,role):
		"""set role"""
		self.role=role

	def setStatus(self,status):
		"""set the status of a certain dude-participant (there are no women on the
		internet, and most certainly not on jabber)"""
		self.status=status
