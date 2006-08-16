# -- coding: utf-8 --
'''
xmpp_abstract.py
///////////////////////////////////////
Abstract layer to xmpp
///////////////////////////////////////
'''

import xmpp
import types

import config
conf=config.Configuration()
mysql=config.MySQL()
import misc
filters=misc.StringFilters()
import user_identification as uids

class PM:
	'''this is a class of a person we're having a conversation with.'''

	def __init__(self,jid,conn,nick=None,permissions=[]):
		'''make the instance ready for use by checking if the user was already known to us and registering him/her in the database if not. the nick attribute allows for a preset nickname to be used. if not specified, the node of the jid will be used instead. the jid may be an xmpp.JID() instance or a string. more specifically, if the jid is an instance, no matter which one, it is not modified. this means that you /could/, technically, supply an instance of your custom JID-class. also takes an instance of the xmpp connection class.'''
		if not type(jid)==types.InstanceType:
			jid=xmpp.JID(jid)
		self.jid=jid
		self.nick = nick or jid.getNode()
		self.conn=conn
		self.permissions=permissions

		self.uid=uids.addUid(jid.getStripped(),'jabber-pm')

	def send(self,message):
		"""send a personal chat message to jid. takes: message (str)"""
		xml=xmpp.Message(to=self.jid,body=message,typ="chat")
		self.conn.send(xml)

	def getJid(self):
		'''fetch the jid of the user. returns an xmpp.JID() instance'''
		return self.jid

	def getNick(self):
		'''return the nick of the person in a string'''
		return self.nick

	def getPermissions(self):
		'''return an iterable object with the permissions of this user (this is currently a list, but that might change)'''
		return self.permissions

	def getUid(self):
		'''if you don't understand this one... then...'''
		return self.uid

	def isAllowedTo(self,plok):
		'''return True if this contact is allowed to do plok (str)'''
		for elem in self.getPermissions():
			if elem in ('all',plok):
				return True
		else:
			return False


class MUC:
	'''this class will let you create a muc-room object. you can use that object to do room-specific tasks, like sending a message, changing the mood of that room, get the participants, change the nickname, etcetera.

self.participants is a dictionary that holds all the members of the room and info about them. their nick (as string) is used as key and an instance of MUCParticipant is used as the content. use the self.getParticipants() functions (and other related ones) to access this list rather than accessing it directly.

temp: currently, it's just a dictionary with nicknames as keys and empty values (None). this will change soon.'''



	def __init__ ( self, jid, conn, nick= conf.misc['bot_nickname'], autojoin= True, mood=70, trydifferentnick= True , behaviour = 'normal' ) :
		'''declare some variables and join the room.
takes:
- jid (xmpp.JID() || str): the jid of the room (fucking-duuh!)
- the infamous connection instance...
- nick (str): the preferred nickname of the bot
- autojoin (bool): whether or not to join immediately when the instance is created
- mood (int): the mood-level that goes with this room
- trydifferentnick (bool): whether or not to retry if the nick is already taken #fixme: make this work
- behaviour (str): our behaviour in this room'''

		self.mood=mood
		self.participants={}
		self.nick=nick
		self.jid=xmpp.JID(jid)
		self.active=False #set to True when we are in this room
		self.setBehaviour(behaviour)
		self.participants=[]
		self.conn=conn
		if autojoin:
			self.join(silent=True)
		self.uid=uids.addUid(jid.getStripped(),'jabber-muc')


	def __str__(self):
		'''return the jid of the room as a string'''
		return self.jid.__str__()




	def join(self,silent=True,force=False):
		"""join a muc room. more precisely; send presence to it.

takes:
- silent (bool): control return behaviour
- force (bool): don't stop if we are already in there

fixme: return True on success and False (or error message) on failure"""



		if self.active and not force:
			if silent:
				return False
			else:
				return "ah that didn't work out.. it seems I'm already in that room"

		#<presence to="jid/nick">
		#<show>online</show>
		#<status>online</status>
		#<x xmlns="http://jabber.org/protocol/muc" />
		#</presence>

		# to : room@conference-server/nickname
		#(jid: node@domain/resource)


		jid=self.jid
		jid.setResource(self.nick)

		xml=xmpp.Presence(show='online',status="online")
		xml.setTo(jid.__str__())
		#add <x xmlns="http://jabber.org/protocol/muc" />
		xml.addChild('x',namespace='http://jabber.org/protocol/muc')

		#from here on we don't need the nickname anymore:
		jid.setResource(None)

		self.conn.send(xml)
		self.active=True

		if silent:
			return True
		else:
			return "k."



	def leave(self,message=True,silent=False,force=False):
		"""leave the muc room. sends the message

takes:
- conn (xmpp.Client()) : xmpp connection instance to use to leave the room
- message (bool) : if True, send a (hardcoded) goodbye message to the room before leaving
- silent (bool) : return True (bool) instead of message (str) if silent == True
- force (bool) : don't return if we are already in the room

returns:
- True (bool) : if silent==True , no matter if the function actually failed or not
- message (str) : if silent==False (same as above)."""

		stripped_jid = self.jid.getStripped()
		if not self.isActive() and not force:
			return "I'm not in that room anyway"
		if message:
			self.send("sorry guys, gotta go ")
			self.send("bye!")
		xml=xmpp.Presence(to=stripped_jid,typ='unavailable')
		self.conn.send(xml)
		self.setInActive()
		return silent or "k."



	def send(self,message):
		"""send a message to the room.
takes: message (str), the message to send"""

		num_n=message.count('\n') #fixme: are there other possibilities of inserting newlines?
		num_chars=message.__len__()
		if num_n > 2 or num_chars > 255:
			#note that we just expect this to occur when someone asked something; this function is also called
			#internally though. so, we better watch out not to have (error) messages trigger this, or it'll
			#look helluva weird for the other occupiants :)
			message = "sorry, if I'd react to that here it would spam the room too much. talk to me in PM"

		xml=xmpp.Message(to=self.jid,body=message,typ='groupchat')
		self.conn.send(xml)



	def addParticipant(self,participant,force=False):
		'''add a participant to the pool of participants. if force==True, don't return False if the participant already exists.'''
		if not force and participant in self.participants:
			return False
		else:
			self.participants.append(participant)

	def delParticipant(self,nick):
		'''delete a user from the list of participants'''
		for elem in self.participants:
			if elem.nick==nick:
				self.participants.remove(elem)
				break #no need to continue.


	def getBehaviour(self,asstring=False):
		'''return the behaviour we have in this room as an integer. If asstring==True (bool) return a string instead.'''
		if asstring:
			return config.Misc.behaviour[self.behaviour]
		else:
			return self.behaviour

	def getJid(self,asstring=False):
		'''return the jid of this room as an xmpp.JID() instance. if string==True, return it as a string'''
		if asstring:
			return self.jid.__str__()
		else:
			return self.jid

	def getMood(self):
		'''return the mood value of this room'''
		return self.mood

	def getNick(self):
		'''return the nick we have in this chatroom'''
		return self.nick

	def getParticipant(self,nick):
		'''return the instance of the participant with this nick (str). note; this really raises a KeyError exception if there's no such participant'''
		return self.participants[nick]

	def getParticipants(self):
		'''return a tuple with all the participants'''
		result=()
		for elem in self.participants:
			result+=(elem.__str__(),)
		return result

	def getUid(self):
		'''return the uid (int) of this room.'''
		return self.uid


	def isActive(self):
		'''return a boolean that indicates whether we are or are not in this room'''
		return self.active

	def isParticipant(self,nick):
		'''return True if nick is a participant of the room, False if not'''
		return nick in self.participants

	def setActive(self):
		'''set the self.active value to True (bool)'''
		self.active=True

	def setBehaviour(self,behaviour):
		'''set the behaviour of the group to a specified level. takes a string or an integer. note that when a string is supplied, it will try to get the appropriate integer from config.Misc.behaviour. if none is found, a ValueError will be raised.'''
		try:
			behaviour=int(behaviour) #this recognises '1' as an integer too
		except ValueError: #this is the exception for int('non-numerical-string')
			for elem in config.Misc.behaviour.iteritems():
				if elem[1]==behaviour:
					return self.setBehaviour(elem[0])
			#if we've gotten up till here, it means the above didn't return anything and the supplied behaviour doesn't exist:
			raise ValueError, "Behaviour could not be found"
		else:
			#it's an integer now, but we gotta make sure it's a valid one:
			if not behaviour in config.Misc.behaviour:
				raise ValueError, "Behaviour could not be found"
			else:
				self.behaviour=behaviour

	def setInActive(self):
		'''inverse of self.Active()'''
		self.active=False




## end of class MUC ##



#temp: stub for what the MUCParticipant class will look like

class MUCParticipant:
	'''a member of a groupchat. it holds information like wether he/she is an admin, what his/her nickname is, etcetera.'''

	def __init__(self,nick,role,status,jid=None):
		'''create the values that will be needed later on'''
		self.nick=nick
		self.status=status
		self.role=role
		if jid:
			self.jid=xmpp.JID(jid)

	def getJid(self):
		'''return participant's jid as an xmpp.JID() instance'''
		return self.jid

	def getNick(self):
		'''return participant's nickname'''
		return self.nick

	def getRole(self):
		'''return participant's role'''

	def getStatus(self):
		'''return participant's status'''
		return self.status

	def isActive(self):
		'''check if a participant is active. it is not uncommon, though, to expect this to be True if the instance is present without checking.'''
		if self.status!='unavailable':
			return True
		else:
			return False

	def isAdmin(self):
		'''return True (bool) if participant's role is admin. useful for interoperability with other protocols.'''
		if self.role == 'moderator':
			return True
		else:
			return False

	def isOnline(self):
		'''alias for self.isActive() '''
		return self.isActive()

	def setNick(self,nick):
		'''set the nickname'''
		self.nick=nick

	def setRole(self,role):
		'''set role'''
		self.role=role

	def setStatus(self,status):
		'''set the status of a certain dude-participant (there are no women on the internet, and most certainly not on jabber)'''
		self.status=status




class MUCRooms:
	'''use this class to handle the whole collection of MUC-rooms known to us'''


	def join(self,jid,conn):
		'''join a muc room. use the existing instance if available, create a new one if not.
note: if you want more flexible joining (for example; setting autojoin to False, chaging some values before joining, etcetera), you can do this instead:
- create the new room with self.new first, setting autojoin=False
- get the instance of the new room with self.getByJid()
- suit that instance to fit your needs
- use its join() method to finally join the room'''
		if not type(jid)==types.InstanceType:
			jid=xmpp.JID(jid)
		try:
			room=self.getByJid(jid)
			message=room.join(silent=False)
		except ValueError:
			result=self.new(jid,conn)
			#if the above succeeded, result should now be an instance of the room that was joined
			if type(result)==types.InstanceType:
				message="k."
			else:
				message="ehmm... error?"
		return message


	def leave(self,jid):
		'''leave a muc room. self.getByJid()'s return value is not checked, so if the room is not a known one, you'll get a ValueError. '''
		self.getByJid(jid).leave()




	def new(self,jid,conn,silent=True,autojoin=True):
		'''add a room with a specified jid to the list and join it automatically (unless autojoin==False). return its instance.'''
		if self.isExistant(jid):
			if silent:
				return False
			else:
				return "Im already in this room.."
		newroom=MUC(jid,conn,autojoin=autojoin)
		config.Misc.rooms.append(newroom)
		return newroom

	def remove(self,jid,silent=True):
		'''remove a room with this jid from the list'''
		try:
			room=self.getByJid(jid)
		except ValueError:
			if silent:
				return False
			else:
				return "I don't know that room anyway..."

		message=room.leave()
		config.Misc.rooms.remove(room)
		return message


	def getActive(self):
		'''return a tuple with all instances of rooms that are active (also look at self.getAll() )'''
		result=()
		for elem in config.Misc.rooms:
			if elem.isActive():
				result+=(elem,)
		return result

	def getAll(self):
		'''return a tuple with all instances of the known rooms (you will generally want to use self.getActive() )'''
		result=()
		for elem in config.Misc.rooms:
			result+=(elem,)
		return result


	def getByJid(self,jid):
		'''return the room instance by providing it's jid (xmpp.JID() instance or string). raises a ValueError if not found.'''
		jid=xmpp.JID(jid)
		for elem in config.Misc.rooms:
			if jid.bareMatch(elem.getJid()):
				return elem
		#if we get up to here, there is no such room
		raise ValueError


	def isExistant(self,jid):
		'''return True if a specified jid is known to us as a muc room, return False if it isn't (similar to getByJid(), but not entirely the same)'''
		jid=xmpp.JID(jid)
		for elem in config.Misc.rooms:
			if elem.getJid()==jid:
				return True
			else:
				return False

	def isActive(self,jid):
		'''similar to self.isExistant(), but slightly different: only return True (bool) if the room is not only known but also active'''
		jid=xmpp.JID(jid)
		for elem in config.Misc.rooms:
			if elem.getJid()==jid and elem.isActive():
				return True
			else:
				return False



pass