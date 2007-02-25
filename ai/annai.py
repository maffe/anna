"""The 'official' AI module for Anna (english)."""

from random import randint
import re
import types
import sys

#TODO: this importing is all quite a mess..
import admin
import stringfilters as filters
import stats
import config
import pluginhandler
from user_identification import isAllowedTo as uidIsAllowedTo
import aihandler
import frontendhandler
import rooms

#pre-compiled regular expressions
_REX_PM_LEAVE_MUC = re.compile("((please )?leave)|(exit) ", re.IGNORECASE)

#this dictionary is used to store the replacement values for messages
#in a muc that use placeholders, like %(nick)s and %(user)s.
#TODO: this is GODDAMNED UGLY, k? kk.
_muc_replace_dictionary = {}


def direct(message, identity):
	"""A message directed specifically towards the bot."""

	typ = identity.getType()
	reply = None
	uid = identity.getUid()
	message = filters.xstrip(message)

	if identity.isAllowedTo("stop") and message == "stop":
		identity.send("k")
		admin.stop()
		return

	elif message[:12] == "load module " and message[12:]:
		#prevent trying to load an empty module
		result = aihandler.setAID(uid, message[12:])
		#note about this line; make sure to prevent injection attacks
		#in aihandler.setAID() by checking the second argument!
		if   result == 0:
			reply = "success!"
		elif result == 1:
				reply = "no such module"

	if message.lower() == "stats":
		reply = stats.simple()
	elif message.lower() == "extended stats":
		reply = stats.extended()
	elif message.lower() == "rooms":
		reply = stats.rooms()

	if reply:
		#replace some stuff in the reply:
		replacedict = {'user': identity.getNick()}
		try:
			reply = reply % replacedict
		except KeyError, e:
			if e[0] == "nick":
				reply = 'I was told to say "%s" now but since this is a' % reply \
				      + ' private conversation it seems awkward to replace' \
							+ ' %(nick)s by something...'
			else:
				reply = 'I was told to say "%s" now but I' % reply \
				      + " don't know what to replace %%(%s)s with" % e[0]
		except StandardError, e:
			reply = 'I was taught to say "%s" now, but there seems' % reply \
			      + ' to be something wrong with that..'

	if not reply and message[:5] == "join ":
		temp = message[5:].split()

		#what type is it? if none specified, assume type of calling frontend
		if len(temp) > 2 and temp[-2] == "type":
			roomType = temp[-1]
			temp = temp[:-2]
		else:
			roomType = typ

		if not frontendhandler.existsTyp(roomType):
			reply = "no such type: %s" % typ

		#see if a certain nick was specified:
		if len(temp) > 2 and temp[-2] == "as":
			nick = temp[-1]
			temp = temp[:-2]
		else:
			nick = config.misc['bot_nickname']

		roomID = ' '.join(temp)

		if rooms.isActive(roomID, roomType):
			reply = "excusez moi, but je suis already in there"

		room = rooms.new(roomID, roomType)
		room.setNick(nick)
		room.join()
		room.send("lo, Im a chatbot. was told to join this room by %s" % identity)
		reply = "k"
	#end if "join such and such room"

	if not reply and re.match(_REX_PM_LEAVE_MUC, message):
		temp = re.sub(_REX_PM_LEAVE_MUC, '', message, 1).split()
		#match either "forcefully" or "forcefully!"
		if temp[-1].strip('!') == "forcefully":
			force = True
			temp.pop()
		else:
			force = False

		#determine the type
		if len(temp) > 3 and ' '.join(temp[-3:-1]) == "of type":
			roomType = temp[-1]
			temp = temp[:-3]
		else:
			roomType = typ

		if not frontendhandler.existsTyp(roomType):
			reply = "no such type"
		
		roomID = ' '.join(temp)
		if not rooms.exists(roomID, roomType):

			if force:
				#rooms.new() returns existing instance if present
				room = rooms.new(roomID, roomType)
				room.send("Sorry guys, %s told me to leave. Bye." % identity)
				rooms.remove(roomID, roomType)
				reply = "k."
			else:
				reply = 'Meh, I wasn\'t even in there. say "leave %s of type %s' % (roomID, typ) + \
				        ' forcefully" if you want me to try and leave that anyway.'
		else:
			room = rooms.get(roomID, roomType)
			room.send("Sorry guys, %s told me to leave. Bye." % identity)
			#rooms.remove() calls the .leave method
			rooms.remove(roomID, roomType)
			reply = "k."
	
	if not reply:
		#handlePlugins() does not actually apply plugins; just checks commands to
		#moderate them
		reply = handlePlugins(message, uid)
	
	try:
		plugins = identity.getPlugins()
	except ValueError:
		plugins = pluginhandler.getDefaultPM()
		identity.setPlugins(plugins)
	for plugin in plugins:
		#.process needs a reply=None if no reply, and that's default, so it's ok.
		message, reply = plugin.process(identity, message, reply)

	if reply:
		identity.send(reply)


def room(message, sender, room):
	"""Use this function to get yourself a reply that fits a mutli user
	chat message.

	- If the message starts with the current nickname followed by a
	  highlighting character, handle it with mucHighlight().
	- Call all loaded modules.
	- If any of the above gave a result by setting the "message" variable,
	  send that very variable back to the room with muc.send().
		
	"""
	typ = room.getType()
	nickname = room.getNick()
	_muc_replace_dictionary['user'] = sender.getNick()
	_muc_replace_dictionary['nick'] = room.getNick()

	if sender.getNick().lower() == nickname.lower():
		return False  #prevent loops
	message = filters.xstrip(message)
	reply = None

	# Handle messages with leading nick as direct messages.
	for elem in config.Misc.hlchars:
		# Check if we have nickanme + one hlchars
		prefix = nickname + elem
		if message[:len(prefix)] == prefix:
			return mucHighlight(message, sender, room)
	
	# Apply plugins.
	try:
		plugins = room.getPlugins()
	except ValueError:
		plugins = pluginhandler.getDefaultMUC()
		room.setPlugins(plugins)
	for plugin in plugins:
		message, reply = plugin.process(room, message, reply)

	if reply and room.getBehaviour() != 0:
		if (reply.count('\n') > 2 or len(reply) > 255) and room.getBehaviour() < 3:
			room.send("Sorry, if I would react to that it would spam the room too"
			         + " much. Please repeat it to me in PM.")
		else:
			room.send(reply)


def mucHighlight(message, sender, room):
	"""This is for when highlighted in a groupchat."""

	reply = None
	uid = room.getUid()
	nick = room.getNick()
	#TODO: we just 'assume' the highlight character to be of length 1 here
	hlchar = message[len(nick)]
	# Strip the leading nickname and hlcharacter off.
	message = message[(len(nick) + 1):].strip()
	# Set to True if the nickname shouldn't be prepended to the reply.
	#TODO: ...huh? when is this set to True then?
	raw = False

	if message == "please leave":
		room.send("... :'(")
		room.leave()
		return

	elif message[:4] == "act ":
		try:
			room.setBehaviour(getBehaviourID(message[4:]))
			reply = "k."
		except ValueError:
			reply = "behaviour not found"

	elif message[:24] == "change your nickname to ":
		room.changeNick(message[24:])

	elif message[:12] == "load module " and message[12:]:
	#the "and message[12:]" prevents trying to load an empty module
		result = aihandler.setAID(uid, message[12:]) #TODO: security?
		if result == 0:
			reply = "success!"
		elif result == 1:
			reply = "no such module"
	elif message == "what's your behaviour?":
		#TODO: this wil crash the bot if room.getBehaviour() returns a false value.
		#bug or feature?
		reply = getBehaviour(room.getBehaviour())

	if not reply:
		reply = handlePlugins(message, uid)

	for plugin in sender.getPlugins():
		message, reply = plugin.process(room, message, reply)

	if reply and room.getBehaviour() != 0:

		if not raw:
			#pick a random highlighting char:
			#TODO: UGLY UGLY UGLY UGLY UGLY UGLY UGLY!!!!!
			n = randint(0, len(config.Misc.hlchars) - 1)
			hlchar = config.Misc.hlchars[n]
			del n
			reply = "%s%s %s" % (sender.getNick(), hlchar, reply)

		#TODO: check if newlines can be inserted in another way
		if (reply.count('\n') > 2 or len(reply) > 255) and room.getBehaviour() < 3:
			room.send("Sorry, if I would react to that it would spam the room too"
			         + " much. Please repeat it to me in PM.")
		else:
			room.send(reply)


def mucReplaceString(message):
	"""this function replaces the message with elements from the dict. if
	an error occurs (eg.: due to wrong formatting of the message) it is
	catched and an appropriate message is returned.

	this is defined in a seperate function because the same thing (this)
	is done twice; once in room() and once in mucHighlight().

	because mucHighLight() doesn't know the name of the other person (and
	because of flexibility issues) the replacedictionary is"""

	try:
		return message % _muc_replace_dictionary

	except KeyError, e:
		return """I was told to say "%s" now but I don't know what to""" % message + \
		       """replace %%(%s)s with""" % e[0]

	except StandardError, e:
		return 'I was taught to say "%s" now, but there seems to be' % message + \
		       'something wrong with that..'





def handlePlugins(message, uid):
	"""Checks if the message wants to modify plugin settings and applies
	them to given uid."""
	if message.startswith("load plugin "):
		try:
			pluginhandler.addPlugin(uid, message[12:])
			return "k."
		except ValueError:
			return "plugin not found."
	
	if message.startswith("unload plugin "):
		try:
			pluginhandler.removePlugin(uid, message[14:])
			return "k."
		except ValueError:
			return "plugin not found."

	if message.lower() == "list plugins":
		try:
			plugins = pluginhandler.getPlugins(uid)
			return "plugins:\n- " + "\n- ".join([plugin.ID for plugin in plugins])
		except ValueError:
			return "no plugins loaded"

	if message.lower() == "list available plugins":
		#TODO: nice textual representation of this iterable element
		return str(pluginhandler.getAllPlugins())

	#if it wasn't anything, return None.
	return None


def invitedToMuc(room, situation, by = None, reason = None):
	"""handler to call if invited to a muc room.
	takes:
		- room: the instance of the (unjoined room)
		- situation: the situation we are in and the reason for the invitation.
		  situations:
		  0) already active in room: return an excuse message to the room
		  1) room known, but inactive: join it and say thx 4 inviting
		  2) room unknown: create it, join it and say thx
		- by: a unicode containing the name of the person that invited the bot
		- reason: unicode containing the reason for the invite as supplied by
		  the inviter
	technically speaking, the by and reason attributes are valid as long as
	they have a .__str__() method. of course, unicode should be used throughout
	the entire bot, but it's not necessary."""
	
	#this dictionary holds all the messages that could be sent. it's not very
	#nice because you construct them all even though one is going to be used,
	#but since this is called not very often I thought it would be nice,
	#because it also improves readability. also note that right now the indexes
	#are the situation codes, but that could very well be changed.
	messages = {}
	if reason:
		messages[0] = "I was invited to this room, being told '%s'," % reason \
		            + "but I'm already in here..."
	else:
		messages[0] = "I was invited to this room again but I'm already in here..."
	#below we also mention who invited to show the admins of the muc.
	messages[1] = "Hey all. Thanks for inviting me again, %s." % by
	messages[2] = "Lo, I'm a chatbot. I was invited here by %s." % by

	if situation != 0:
		room.join()

	room.send(messages[situation])


# a directory representing the different behaviour-levels and their textual representations
behaviour = {
0:'silent',# with this behaviour you should typically not say anything
1:'shy'   ,# only talk when talked to
2:'normal',# react to everything you can react to, even if not addressed
3:'loud'   # say random things at random moments, be annoying
}

def getBehaviour(id):
	return behaviour[id]

def getBehaviourID(text):
	"""get the numerical ID of the specified behaviour"""
	for elem in behaviour.iteritems():
		if elem[1] == text:
			return elem[0]
	raise ValueError, text

def isBehaviour(arg):
	"""returns True if supplied behaviour (textual OR numerical) is valid."""
	return type(arg) == types.IntType and (arg in behaviour) or (arg in behaviour.values())
