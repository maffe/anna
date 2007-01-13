# -- coding: utf-8 --
'''english localisation for anna'''

from random import randint
import re
import types
import sys


#TODO: this importing is all quite a mess..

import factoids_reactions
Factoids = factoids_reactions.Factoids()
ReactionsGlobal = factoids_reactions.ReactionsGlobal()
ReactionsDirect = factoids_reactions.ReactionsDirect()

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
_REX_PM_LEAVE_MUC = re.compile( "((please )?leave|exit) ", re.IGNORECASE )

#this dictionary is used to store the replacement values for messages
#in a muc that use placeholders, like %(nick)s and %(user)s.
#TODO: this is GODDAMNED UGLY, k? kk.
_muc_replace_dictionary = {}

def direct( message, identity, typ ):
	'''a message directed specifically towards us'''

	reply   = None
	uid     = identity.getUid()
	message = filters.xstrip( message )


	if identity.isAllowedTo( "stop" ) and message == "stop":
		identity.send( "k" )
		admin.stop()
		return

	elif message[:12] == "load module " and message[12:]:
		#prevent trying to load an empty module
		result = aihandler.setAID( uid, message[12:] )
		#note about this line; make sure to prevent injection attacks
		#in aihandler.setAID() by checking the second argument!
		if   result == 0:
			reply = "success!"
		elif result == 1:
			reply = "no such module"

	elif identity.isAllowedTo( "protect" ) and message[:8] == "protect ":
		message = message[8:]

		if   message[:16] == "the reaction to ":
			result = ReactionsGlobal.protect( message[16:], silent=False )
		elif message[:12] == "reaction to ":
			result = ReactionsGlobal.protect( message[12:], silent=False )
		elif message[:8]  == "factoid ":
			result = Factoids.protect( message[8:], silent=False )
		else:
			result = Factoids.protect( message, silent=False )

		if result   == 0:
			reply = "k."
		elif result == 1:
			reply = "I don't know what that is"
		elif result == 2:
			reply = "database error: query failed"
		elif result == 3:
			reply = "I know, it's already set up that way"
		else:
			reply = "uhh.. error?"


	if message.lower() == "stats":
		reply = stats.simple()
	elif message.lower() == "extended stats":
		reply = stats.extended()
	elif message.lower() == "rooms":
		reply = stats.rooms()

	#fixme: need a more elegant solution
	if not reply:
		reply = handleProtection(message)
		if not reply:
			reply = handleReactions(message,uid)
			if not reply:
				#reply = handleFactoids(message,uid)
				if not reply:
					reply = ReactionsDirect.get(message)
					if not reply or type(reply) == types.IntType:
						reply = ReactionsGlobal.get(message)
						if type(reply) == types.IntType:
							reply = None

		if reply:
			#replace some stuff in the reply:
			replacedict={'user':identity.getNick()}
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
		message = message[5:].split()

		#what type is it? if none specified, assume type of calling frontend
		if len( message ) > 2 and message[-2] == "type":
			roomType = message[-1]
			message = message[:-2]
		else:
			roomType = typ

		if not frontendhandler.existsTyp( roomType ):
			reply = "no such type: %s" % typ

		#see if a certain nick was specified:
		if len( message ) > 2 and message[-2] == "as":
			nick = message[-1]
			message = message[:-2]
		else:
			nick = config.misc['bot_nickname']

		roomID = ' '.join( message )

		if rooms.isActive( roomID, roomType ):
			reply = "excusez moi, but je suis already in there"

		room = rooms.new( roomID, roomType )
		room.setNick( nick )
		room.join()
		room.send( "lo, Im a chatbot. was told to join this room by %s" % identity )
		reply = "k"
	#end if "join such and such room"

	if not reply and re.match( _REX_PM_LEAVE_MUC, message ):
		message = re.sub( _REX_PM_LEAVE_MUC, '', message, 1 ).split()
		#match either "forcefully" or "forcefully!"
		if message[-1].strip('!') == "forcefully":
			force = True
			message.pop()
		else:
			force = False

		#determine the type
		if len( message ) > 3 and ' '.join( message[-3:-1] ) == "of type":
			roomType = message[-1]
			message = message[:-3]
		else:
			roomType = typ

		if not frontendhandler.existsTyp( roomType ):
			reply = "no such type"
		
		roomID = ' '.join( message )
		if not rooms.exists( roomID, roomType ):

			if force:
				#rooms.new() returns existing instance if present
				room = rooms.new( roomID, roomType )
				room.send( "Sorry guys, %s told me to leave. Bye." % identity )
				rooms.remove( roomID, roomType )
				reply = "k."
			else:
				reply = 'Meh, I wasn\'t even in there. say "leave %s of type %s' % (roomID, typ) + \
				        ' forcefully" if you want me to try and leave that anyway.'
		else:
			room = rooms.get( roomID, roomType )
			room.send( "Sorry guys, %s told me to leave. Bye." % identity )
			#rooms.remove() calls the .leave method
			rooms.remove( roomID, roomType )
			reply = "k."
	
	if not reply:
		#handlePlugins() does not actually apply plugins; just checks commands to moderate them
		reply = handlePlugins( message, uid )
	
	for plugin in pluginhandler.getPlugins( uid ):
		#.process needs a reply=None if no reply, and that's default, so it's ok.
		message, reply = plugin.process( identity, message, reply )

	if reply:
		identity.send( reply )




def room( message, sender, typ, room ):
	'''use this function to get yourself a reply that fits a mutli user
chat message.

- if the message starts with the current nickname followed by a
  highlighting character, handle it with mucHighlight()
- check if someone asked for a factoid, by filtering "what is", "?", etc.
- finally, if all else failed, check if there's a reaction connected to
  this message
- if any of the above gave a result by setting the "message" variable,
  send that very variable back to the room with muc.send()'''



	nickname = room.getNick()
	_muc_replace_dictionary['user'] = sender
	_muc_replace_dictionary['nick'] = room.getNick()

	if sender.lower() == nickname.lower():
		return False  #prevent loops
	message = filters.xstrip( message )
	reply = None

	#handle messages with leading nick as direct messages
	for elem in config.Misc.hlchars:
		# Check if we have nickanme + one hlchars
		prefix = nickname + elem
		if message[:len(prefix)] == prefix:
			return mucHighlight( message, sender, room )
	
	#if reply is set, skip the checks. also skip this stuff if the
	#behaviour is "silent" or "shy" (shy means only react when addressed!)
	#TODO: make this look better (regexp?)
	if not reply and room.getBehaviour() > 1:
		if message.lower()[:8] == "what is ":
			reply = Factoids.get( filters.stripQM( message[8:] ) )
	
		elif message.lower()[:7] == "what's " :
			reply = Factoids.get( filters.stripQM( message[7:] ) )
	
		elif message[-1:]        == "?":
			reply = Factoids.get( message[:-1] )
	
		if type(reply) == types.IntType:
			#if error
			reply = None
			#ignore


	#if we still don't have anything to say, AND if we aren't "silent" OR "shy",
	#try some more global reactions.
	if not reply and room.getBehaviour() > 1:
		reply = ReactionsGlobal.get( message )
		if reply: #if there was no reaction don't bother doing anything else
			if type( reply ) == types.IntType: #if an error ocurred
				reply = None #ignore it
			else:
				reply = mucReplaceString( reply )

	#apply plugins
	for plugin in pluginhandler.getPlugins( room.getUid() ):
		message, reply = plugin.process( room, message, reply )

	if reply and room.getBehaviour() != 0:
		if (reply.count( '\n' ) > 2 or len( reply ) > 255) and room.getBehaviour() < 3:
			room.send( "Sorry, if I would react to that it would spam the room too"
			         + " much. Please repeat it to me in PM." )
		else:
			room.send( reply )



def mucHighlight( message, sender, room ):
	'''This is for when highlighted in a groupchat.'''

	reply = None
	uid = room.getUid()
	nick = room.getNick()
	#TODO: we just 'assume' the highlight character to be of length 1 here
	#TODO: don't prefix above comment with "TODO" ;P
	hlchar = message[ len(nick) ]
	#strip the leading nickname and hlcharacter off
	message = message[ len(nick) + 1 : ].strip()
	#set to True if the nickname shouldn't be prepended to the reply
	raw = False

	if message == "please leave":
		room.send( "... :'(" )
		room.leave()
		return

	elif message[:4] == "act ":
		try:
			room.setBehaviour( getBehaviourID( message[4:] ) )
			reply = "k."
		except ValueError:
			reply = "behaviour not found"

	elif message[:24] == "change your nickname to ":
		room.changeNick( message[24:] )

	elif message[:12] == "load module " and message[12:]:
	#the "and message[12:]" prevents trying to load an empty module
		result = aihandler.setAID( uid, message[12:] ) #TODO: security?
		if result == 0:
			reply = "success!"
		elif result == 1:
			reply = "no such module"
	elif message == "what's your behaviour?":
		#TODO: this wil crash the bot if room.getBehaviour() returns a false value.
		#bug or feature?
		reply = getBehaviour( room.getBehaviour() )

	if not reply:
		reply = handlePlugins( message, uid )


	if not reply:
		reply = handleProtection( message )
		if not reply:
			reply = handleReactions( message, uid )
			if not reply:
				#reply = handleFactoids( message, uid )
				#otheriwse, check for reaction
				if not reply:
					reply = ReactionsDirect.get( message )
					if type( reply ) not in types.StringTypes:
					#ReactionsDirect.get() returns a integer upon error.
						reply = ReactionsGlobal.get( message )
						#ignore the not-found error (1)
						if type( reply ) == types.IntType:
							#for the sake of < python2.5
							reply = ( reply == 1 and (None,) or ("an error occured.",) )[0]
							#python 2.5:
							#reply = None if reply == 1 else "an error occured."
						else:
							raw = True #don't address the sender if it was a global reaction

					#check again because it might have changed in the meanwhile
					if reply:
						reply = mucReplaceString( reply )

	#apply plugins
	for plugin in pluginhandler.getPlugins( uid ):
		message, reply = plugin.process( room, message, reply )


	if reply and room.getBehaviour() != 0:

		if not raw:
			#pick a random highlighting char:
			#TODO: UGLY UGLY UGLY UGLY UGLY UGLY UGLY!!!!!
			n = randint( 0, len( config.Misc.hlchars ) - 1 )
			hlchar = config.Misc.hlchars[n]
			del n
			reply = "%s%s %s" % (sender, hlchar, reply)

		#TODO: check if newlines can be inserted in another way
		if (reply.count( '\n' ) > 2 or len( reply ) > 255) and room.getBehaviour() < 3:
			room.send( "Sorry, if I would react to that it would spam the room too"
			         + " much. Please repeat it to me in PM." )
		else:
			room.send( reply )


def mucReplaceString(message):
	'''this function replaces the message with elements from the dict. if
	an error occurs (eg.: due to wrong formatting of the message) it is
	catched and an appropriate message is returned.

	this is defined in a seperate function because the same thing (this)
	is done twice; once in room() and once in mucHighlight().

	because mucHighLight() doesn't know the name of the other person (and
	because of flexibility issues) the replacedictionary is'''

	try:
		return message % _muc_replace_dictionary

	except KeyError, e:
		return '''I was told to say "%s" now but I don't know what to''' % message + \
		       '''replace %%(%s)s with''' % e[0]

	except StandardError, e:
		return 'I was taught to say "%s" now, but there seems to be' % message + \
		       'something wrong with that..'





def handlePlugins( message, uid ):
	'''Checks if the message wants to modify plugin settings and applies
	them to given uid.'''
	if message.lower()[:12] == "load plugin ":
		try:
			pluginhandler.addPlugin( uid, message[12:] )
			return "k."
		except ValueError:
			return "plugin not found."
	
	if message.lower()[:14] == "unload plugin ":
		try:
			pluginhandler.removePlugin( uid, message[14:] )
			return "k."
		except ValueError:
			return "plugin not found."
	
	if message.lower() == "list plugins":
		plugins = pluginhandler.getPlugins( uid )
		if not plugins:
			return "no plugins loaded"
		reply = "plugins:"
		for plugin in plugins:
			#TODO isn't it ugly to access __name__ directly?
			reply += "\n- %s" % plugin.__name__.split('.')[-1]
		return reply
	
	if message.lower() == "list available plugins":
		#TODO: nice textual representation of this iterable element
		return str( pluginhandler.getAllPlugins() )
	
	#if it wasn't anything, return None.
	return None


def handleProtection( message ):
	'''same as handleFactoids(), except this is for protections'''


	if message[:3].lower() == "is " and message[-11:] == " protected?":
		message = message[3:-11]

		#check if we're requesting for protectedness of a reaction:
		dunno = "I don't know what to say to that anyway..."
		if message[:12].lower() == "reaction to ":
			isprotected = ReactionsGlobal.isProtected( message[12:] )
		elif message[:16].lower() == "the reaction to ":
			isprotected = ReactionsGlobal.isProtected( message[16:] )

		#and if not requesting for reactions, assume factoid:
		else:
			if message[:8].lower() == "factoid ":
				message = message[8:]
			isprotected = Factoids.isProtected( message )
			dunno = "I don't even know what %s is..." % message

		#handle the return values (they are the same for factoids and reactions):
		if isprotected == 0:
			return "no"
		elif isprotected == 1:
			return "yes"
		elif isprotected == 2:
			return "ah crap, a database error"
		elif isprotected == 3:
			return dunno
	else:
		return None




def handleReactions(message,uid):
	'''same as handleFactoids, except this one is for reactions. it doesn't
fetch em though! only for adding/deleting em.'''

	reply=None

	#if there's " is " in the message, do more checking.
	if " is " in message:



		def _IS(message,direct):
			'''this function is called internally by handleReactions().
			if globalordirect is False, global is assumed. if True: direct.'''

			try:
				(listenfor, reaction) = \
					[elem.strip() for elem in message.split(" is ",1)]
			except ValueError:
				return "There's an error in that message..."
				#TODO: this vulnerability is probably elsewhere too - no time now!

			if uidIsAllowedTo(uid,'protect'):

				result=None

				if reaction == "protected":
					result = ReactionsGlobal.protect(listenfor)
				elif reaction in ( 'public', 'unprotected' ):
					result = ReactionsGlobal.unProtect( listenfor )
				#TODO: this means you will get the same answer no matter if
				#you protect or unprotect. I don't care, but it could be done nicer.
				if result == None:
					pass
				elif result == 0:
					return "k"
				elif result == 1:
					return "I don't know what to say to that"
				elif result == 2:
					return "ah crap crap crap... database error!"
				elif result == 3:
					return "yeah, I know.."
				else: #unspecified error messages
					return "hmm.. error."

			if reaction[-26:] == " and append a questionmark":
				reaction = reaction[:-26] + '?'

			#by creating a compatible reference with the same name for both
			#situations we can use one block of code to do two things,
			#depending on the situation.
			if direct:
				ReactionsClass=ReactionsDirect
			else:
				ReactionsClass=ReactionsGlobal

			result=ReactionsClass.get(listenfor)
			if result==1: # object is not known yet
				ReactionsClass.add(listenfor,reaction,uid)
				return "k"
			elif result==2:
				return "oh noes, a database error!"
			elif type(result) in types.StringTypes:
				#means that result holds the definition of the object and
				#not an error code
				if result == reaction:
					return "I know"
				else:
					return "but the reaction to %s is %s"%(listenfor,result)
			else: #an unspecified error occured:
				return "uhh... error?"


		#end _IS()


		#determine whether it's a global or direct reaction:
		if message[:12].lower()=="reaction to ":
			reply=_IS(message[12:],True)
		elif message[:19].lower()=="direct reaction to ":
			reply=_IS(message[19:],True)
		elif message[:19].lower()=="global reaction to ":
			reply=_IS(message[19:],False)

		if reply: # don't bother continuing if we already have a reply
			return reply





	def _DEL(listen_for,direct):
		'''delete a reaction. this function is called internally, just like _IS().'''
		if direct:
			result = ReactionsDirect.delete(listen_for)
		else:
			result = ReactionsGlobal.delete(listen_for)

		if result==0:
			return "k"
		elif result==1:
			return "I don't know what that means anyway"
		elif result==3: #this is more likely to happen
			return "that factoid is protected. an admin needs to unprotect it before you can remove it."
		elif result==2:
			return "shit, db error."

	#del global reaction
	if message[:19].lower()=="forget reaction to ":
		return _DEL(message[19:],True)
	elif message[:26].lower()=="forget direct reaction to ":
		return _DEL(message[26:],True)
	elif message[:26].lower()=="forget global reaction to ":
		return _DEL(message[26:],False)
	else:
		return None #don't bother defining the function below; we're not gonna use it anyway




def invitedToMuc( room, situation, by = None, reason = None ):
	'''handler to call if invited to a muc room.
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
	the entire bot, but it's not necessary.'''
	
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

	room.send( messages[ situation ] )


# a directory representing the different behaviour-levels and their textual representations
behaviour = {
0:'silent',# with this behaviour you should typically not say anything
1:'shy'   ,# only talk when talked to
2:'normal',# react to everything you can react to, even if not addressed
3:'loud'   # say random things at random moments, be annoying
}

def getBehaviour( id ):
	return behaviour[id]

def getBehaviourID( text ):
	'''get the numerical ID of the specified behaviour'''
	for elem in behaviour.iteritems():
		if elem[1] == text:
			return elem[0]
	raise ValueError, text

def isBehaviour( arg ):
	'''returns True if supplied behaviour (textual OR numerical) is valid.'''
	return type(arg) == types.IntType and ( arg in behaviour ) or ( arg in behaviour.values() )
