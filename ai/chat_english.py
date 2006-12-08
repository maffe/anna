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

from misc import Admin
admin = Admin()
import stringfilters as filters
import stats
import config
import plugin
from user_identification import isAllowedTo as uidIsAllowedTo
import aihandler
import frontendhandler
import rooms


#pre-compiled regular expressions
_REX_PM_LEAVE_MUC = re.compile( "((please )?leave|exit) ", re.IGNORECASE )


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
		result = aihandler.setAID(uid,message[12:])
		#note about this line; make sure to prevent injection attacks
		#in aihandler.setAID() by checking the second argument!
		if   result == 0:
			reply = "success!"
		elif result == 1:
			reply = "no such module"

	elif identity.isAllowedTo( "protect" ) and message[:8] == "protect ":
		message=message[8:]

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

	#<plugins>
	for command in plugin.plughandlers:
		if message.lower() == command.lower():
			for handler in plugin.plughandlers[command]:
				reply = handler( identity )
	#</plugins>

	#fixme: need a more elegant solution
	if not reply:
		reply = handleProtection(message)
		if not reply:
			reply = handleReactions(message,uid)
			if not reply:
				reply = handleFactoids(message,uid)
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
					reply = 'I was told to say "%s" now but since this is a' \
					      + ' private conversation it seems awkward to replace' \
								+ ' %%(nick)s by something...' % reply
				else:
					reply = '''I was told to say "%s" now but I don't know what''' \
					      + ' to replace %%(%s)s with' % ( reply, e[0] )
			except StandardError, e:
				reply = 'I was taught to say "%s" now, but there seems to be' \
				      + 'something wrong with that..' % reply

	if not reply and message[:5] == "join ":
		message = message[5:].split()

		#what type is it? if none specified, assume type of calling frontend
		if message.__len__() > 2 and message[-2] == "type":
			roomType = message[-1]
			message = message[:-2]
		else:
			roomType = typ

		if not frontendhandler.existsTyp( roomType ):
			identity.send( "no such type: %s" % typ )
			return

		#see if a certain nick was specified:
		if message.__len__() > 2 and message[-2] == "as":
			nick = message[-1]
			message = message[:-2]
		else:
			nick = config.misc['bot_nickname']

		roomID = ' '.join( message )

		if rooms.isActive( roomID, roomType ):
			identity.send( "excusez moi, but je suis already in there" )
			return

		room = rooms.new( roomID, roomType )
		room.setNick( nick )
		room.join()
		room.send( "lo, Im a chatbot. was told to join this room by %s" % identity )
		#TODO maybe using identity.__str__() isn't the best way of indicating who this was
		identity.send( "k" )
		return
	#end if "join such and such room"

	#TODO: compile this regexp once
	if not reply and re.match( _REX_PM_LEAVE_MUC, message ):
		message = re.sub( _REX_PM_LEAVE_MUC, '', message, 1 ).split()
		#match either "forcefully" or "forcefully!"
		if message[-1].strip('!') == "forcefully":
			force = True
			message.pop()
		else:
			force = False

		#determine the type
		if message.__len__() > 3 and ' '.join( message[-3:-1] ) == "of type":
			roomType = message[-1]
			message = message[:-3]
		else:
			roomType = typ

		if not frontendhandler.existsTyp( roomType ):
			identity.send( "no such type" )
			return
		
		roomID = ' '.join( message )
		if not force and not rooms.exists( roomID, roomType ):
			reply = 'Meh, I wasn\'t even in there. say "leave %s of type %s' % (roomID, typ) + \
			        ' forcefully" if you want me to try and leave that anyway.'
		else:
			room = rooms.get( roomID, roomType )
			room.send( "Sorry guys, %s told me to leave. Bye." % identity )
			#rooms.remove() calls the .leave method
			rooms.remove( roomID, roomType )
			reply = "k."

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
	global _muc_replace_dictionary
	_muc_replace_dictionary = {
	 'user': sender,
	 'nick': room.getNick()
	 }

	if sender.lower() == nickname.lower():
		return False  #prevent loops
	message = filters.xstrip( message )
	reply = None

	#handle messages with leading nick as direct messages
	nick_len = nickname.__len__() + 1
	for elem in config.Misc.hlchars:
		# Check if we have nickanme + one hlchars
		if message[:nick_len] == nickname+elem:
			reply = mucHighlight( message[nick_len:].strip(), room, prepend = sender )
			#if silent, don't print the reply
			if room.getBehaviour() == 0:
				reply = None
			#don't bother checking for other highlight-characters
			break

	# GET FACTOID
	#if reply is set, skip the checks. also skip this stuff if the
	#behaviour is "silent" or "shy" (shy means only react when addressed!)
	#TODO: use regexp to make this look better
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


	if reply and room.getBehaviour() != 0:
		room.send( reply )



def mucHighlight( message, room, prepend = None ):
	'''this is for when highlighted in a groupchat. message (str)
is the message WITHOUT all the addressing (for example:
"anna: how are you?" becomes "how are you?").

if the prepend (str) is set, this is prepended to the output
with a random highlight character and a whitespace too, except
for some specific cases (for example, if the reply begins with
"/me ", the value isn't prepended anyway). indeed; this is not
the ideal way of doing things... imo; ideally, this function
should just return the answer and the calling function should
handle prepending anything. on the other hand; this is just a
feature; it makes life easier but needs not be used. if you
want to, just ignore it.'''

	reply = None
	uid = room.getUid()

	if message == "please leave":
		room.send( "... :'(" )
		room.leave()
		return

	elif message[:4] == "act ":
		if not isBehaviour( message[4:] ):
			return "behaviour not found"
		room.setBehaviour( getBehaviourID( message[4:] ) )
		return 'k.'

	elif message[:24] == "change your nickname to ":
		#fixme: this is not the right place for conflict checking;
		#we should catch the error message returned by the conference server
		for elem in room.getParticipants():
			if elem == message[24:]:
				return "that nick is already in use"

		room.setNick(message[24:])
		return #nothing more needs to be done.

	elif message[:12] == "load module " and message[12:]:
	#the "and message[12:]" prevents trying to load an empty module
		result = aihandler.setAID( uid, message[12:] ) #fixme: security?
		if result == 0:
			reply = "success!"
		elif result==1:
			reply = "no such module"
	elif type( re.match( '(what\'s|what is) your behaviour\?$', message ) ) \
		!= types.NoneType:
		#re.match() matches a regexp to the beginning of a string.
		#because of the $ at the end of our regexp this means we
		#only get a match if the entire string exactly matches it.
		return room.getBehaviour()


	if not reply:
		reply = handleProtection( message )
		if not reply:
			reply = handleReactions( message, uid )
			if not reply:
				reply = handleFactoids( message, uid )
				#otheriwse, check for reaction
				if not reply:
					reply = ReactionsDirect.get( message )
					if type( reply ) not in types.StringTypes:
					#ReactionsDirect.get() returns an integer upon error, but we want to ignore errors.
						reply = ReactionsGlobal.get( message )
						#temp:
						if not reply:
							pass
						elif type( reply ) == types.IntType: #if error
							reply = None #ignore
						else:
							prepend = None #don't address the sender if it was a global reaction

					#check again because it might have changed in the meanwhile
					if reply:
						reply = mucReplaceString( reply )


	if reply:

		if prepend:
			#pick a random highlighting char:
			n = randint( 0, config.Misc.hlchars.__len__() - 1 )
			hlchar = config.Misc.hlchars[n]
			del n
			reply = "%s%s %s" % (prepend, hlchar, reply)

		return reply


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








def handleFactoids( message, uid ):
	'''use this function to check if a message is meant to do something
with factoids (change one, add one, etc).'''

	reply = None

	#fetch factoid

	if message[:8].lower() == "what is ":
		reply = Factoids.get(filters.stripQM(message[8:]))
	elif message[:7].lower() == "what's ":
		reply = Factoids.get( filters.stripQM(message[7:]) )
	#TODO: why don't we call filters.stripQM() on the line below?
	elif message[:17].lower() == "do you know what " and message.strip( "?" )[-3:] == " is":
		reply = Factoids.get( message[17:-3] )
	if type(reply) == types.IntType:
		if reply == 1:
			reply = "Idk.. can you tell me?"
		elif reply == 2:
			reply = "whoops... db error :s"
		else: #unspecified error
			reply = "an error ocurred"


	if reply: #if there already is a reply
		pass #don't even bother checking all this stuff

	elif message[-1:] == "?":
		reply = Factoids.get( message[:-1] )
		if type( reply ) == types.IntType:
			reply = None

	#forget factoid
	elif message[:7].lower() == "forget ":
		object = message[7:]
		if object[:5].lower() == "what " and object[-3:] == " is":
			object = object[5:-3]
		result = Factoids.delete( object )
		if result == 0:
			reply = "k."
		elif result == 1:
			reply = "I don't know what %s is" % object
		elif result == 2:
			reply = "woops... database error."
		elif result == 3:
			reply = "srry, protected factoid. only an admin can delete that."


	#add factoid
	elif ' is ' in message:
		(object,definition)=[elem.strip() for elem in message.split(" is ",1)]
		if uidIsAllowedTo(uid,'protect'):

			result=None
			if definition=="protected":
				result=Factoids.protect(object)
			elif definition in ('public','unprotected'):
				result=Factoids.unProtect(object)
			#TODO: this means you will get the same answer no matter if you
			#protect or unprotect. I don't care, but it could be done nicer.
			if result==None:
				pass
			elif result==0:
				reply="k"
			elif result==1:
				reply="I don't know what that means"
			elif result==2:
				reply="ah crap crap crap... database error!"
			elif result==3:
				reply="yeah, I know.."
			else: #unspecified error messages
				reply="hmm.. error."


		if not reply:
			result=Factoids.get(object)
			if result==1: # object is not known yet
				Factoids.add(object,definition,uid)
				reply="k"
			elif result==2:
				reply="oh noes, a database error!"
			elif type(result) in types.StringTypes:
				#the result holds an error code
				if result == definition:
					reply="I know"
				else:
					reply="but... but... %s is %s"%(object,result)


	try:
		return reply
	except NameError:
		return None



def handleProtection(message):
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

			(listenfor,reaction)=[elem.strip() for elem in message.split(" is ",1)]

			if uidIsAllowedTo(uid,'protect'):

				result=None

				if reaction =="protected":
					result=ReactionsGlobal.protect(listenfor)
				elif reaction in ('public','unprotected'):
					result=ReactionsGlobal.unProtect(listenfor)
				#TODO: this means you will get the same answer no matter if
				#you protect or unprotect. I don't care, but it could be done nicer.
				if result==None:
					pass
				elif result==0:
					return "k"
				elif result==1:
					return "I don't know what to say to that"
				elif result==2:
					return "ah crap crap crap... database error!"
				elif result==3:
					return "yeah, I know.."
				else: #unspecified error messages
					return "hmm.. error."

			if reaction[-26:]==" and append a questionmark":
				reaction=reaction[:-26] + '?'

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
	messages[2] = "Lo, I'm a chatbot. I was invitied here by %s." % by

	room.send( messages[ situation ] )
	if situation != 0:
		room.join()


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
	raise KeyError, text

def isBehaviour( arg ):
	'''returns True if supplied behaviour (textual OR numerical) is valid.'''
	return type(arg) == types.IntType and ( arg in behaviour ) or ( arg in behaviour.values() )
