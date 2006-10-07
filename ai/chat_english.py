# -- coding: utf-8 --
'''english localisation for anna'''

from random import randint
import sre
import types


#fixme: this importing is all quite a mess..

import factoids_reactions
Factoids=factoids_reactions.Factoids()
ReactionsGlobal=factoids_reactions.ReactionsGlobal()
ReactionsDirect=factoids_reactions.ReactionsDirect()

from misc import Admin
admin=Admin()
import stringfilters as filters
import stats
import config
import plugin
from user_identification import isAllowedTo as uidIsAllowedTo
import aihandler




# def perm(required,supplied):
# 	'''just a little helper function to determine if someone has the needed permissions, instead of having to type if 'prout' in permissions or 'all' in permissions every time.'''
# 	if required in suppied or 'all' in supplied:
# 		return True
# 	else:
# 		return False




def direct(message,identity,typ):
	'''a message directed specifically towards us'''

	reply=None
	uid=identity.getUid()
	message=filters.xstrip(message)


	if identity.isAllowedTo('stop') and message=="stop":
		#pm.send(identity,"ok, well, I'm leaving...") #fixme: we need a nice and clean solution for this that fits the idea! what about returning a message, waiting till it is delivered and stopping only after that?
		admin.stop()

	#fixme: todo:
	#tell the conversations module about the message
	#conversations.received(message,uid)

	elif message[:12]=="load module " and message[12:]: #prevent trying to load an empty module
		result=aihandler.setAID(uid,message[12:]) #fixme: security?
		if result==0:
			reply="success!"
		elif result==1:
			reply="no such module"


	elif identity.isAllowedTo('protect') and message[:8]=="protect ":
		message=message[8:]
		if message[:16]=="the reaction to ":
			result = ReactionsGlobal.protect(message[16:],silent=False)
		elif message[:12]=="reaction to ":
			result = ReactionsGlobal.protect(message[12:],silent=False)
		elif message[:8]=="factoid ":
			result = Factoids.protect(message[8:],silent=False)
		else:
			result = Factoids.protect(message,silent=False)
		if result==0:
			reply="k."
		elif result==1:
			reply="I don't know what that is"
		elif result==2:
			reply="database error: query failed"
		elif result==3:
			reply="I know, it's already set up that way"
		else:
			reply="uhh.. error?"


	if message.lower()=="stats":
		reply = stats.simple()
	elif message.lower()=="extended stats":
		reply = stats.extended()
	elif message.lower()=="rooms":
		reply = stats.rooms()

	for command in plugin.plughandlers:
		if message.lower()==command.lower():
			for handler in plugin.plughandlers[command]:
				reply=handler(identity)

	#fixme: need a more elegant solution
	if not reply:
		reply=handleProtection(message)
		if not reply:
			reply=handleReactions(message,uid)
			if not reply:
				reply=handleFactoids(message,uid)
				if not reply:
					reply=ReactionsDirect.get(message)
					if not reply or type(reply) == types.IntType:
						reply=ReactionsGlobal.get(message)
						if type(reply)==types.IntType:
							reply=None

		if reply:
			#replace some stuff in the reply:
			replacedict={'user':identity.getNick()}
			try:
				reply=reply%replacedict
			except KeyError, e:
				if e[0]=="nick":
					reply='I was told to say "%s" now but since this is a private conversation it seems awkward to replace %%(nick)s by something...'%reply
				else:
					reply='''I was told to say "%s" now but I don't know what to replace %%(%s)s with'''%(reply,e[0])
			except StandardError, e:
				reply='I was taught to say "%s" now, but there seems to be something wrong with that..'%reply

	if reply:
		identity.send(reply)




def room(message,sender,typ,room):
	'''use this function to get yourself a reply that fits a mutli user chat message.

- if the message starts with the current nickname followed by a highlighting character, handle it as a direct message (just like PM) through self.direct()
- check if someone asked for a factoid, by filtering "what is", "?", etc.
- finally, if all else failed, check if there's a reaction connected to this message
- if any of the above gave a result by setting the "message" variable, send that very variable back to the room with muc.send()'''



	nickname = room.getNick()
	_muc_replace_dictionary={
	 'user':sender,
	 'nick':room.getNick()
	 }
	global _muc_replace_dictionary

	if sender.lower()==nickname.lower():
		return False  #prevent loops
	message=filters.xstrip(message)
	reply=None

	#handle messages with leading nick as direct messages
	nick_len = nickname.__len__()+1
	for elem in config.Misc.hlchars:
		# Check if we have nickanme + one hlchars
		if message[:nick_len]==nickname+elem:
			reply=mucHighlight(message[nick_len:].strip(),room,prepend=sender)
			break


	if reply: #if reply is set, skip the checks.
		pass


	#get factoid
	#fixme: use regexp to make this look better
	elif message.lower()[:8]=="what is ":
		reply=Factoids.get(filters.stripQM(message[8:]))
	elif message.lower()[:7]=="what's " :
		reply=Factoids.get(filters.stripQM(message[7:]))
	elif message[-1:]=="?":
		reply=Factoids.get(message[:-1])
	if type(reply)==types.IntType: #if error
		reply=None #ignore


	if not reply:
		reply=ReactionsGlobal.get(message)
		if reply: #if there was no reaction don't bother doing anything else
			if type(reply)==types.IntType: #if an error ocurred
				reply=None #ignore it
			else:
				reply=mucReplaceString(reply)


	if reply and room.getBehaviour(): #if silent: don't speak

		room.send(reply)



def mucHighlight(message,room,prepend=None):
	'''this is for when highlighted in a groupchat. message (str) is the message WITHOUT all the addressing (for example: "anna: how are you?" becomes "how are you?").

if the prepend (str) is set, this is prepended to the output with a random highlight character and a whitespace too, except for some specific cases (for example, if the reply begins with "/me ", the value isn't prepended anyway). indeed; this is not the ideal way of doing things... imo; ideally, this function should just return the answer and the calling function should handle prepending anything. on the other hand; this is just a feature; it makes life easier but needs not be used. if you want to, just ignore it.'''

	reply=None
	uid=room.getUid()

	if message=="please leave":
		room.send("... :'(")
		room.leave(message=False,silent=True)
		return
	elif message[:4]=="act ":
		behaviour=getBehaviourID(message[4:])
		if behaviour==None:
			return "behaviour not found"
		room.setBehaviour(behaviour)
		return 'k.'

	elif message[:24]=="change your nickname to ":
		#fixme: this is not the right place for conflict checking; we should catch the error message returned by the conference server
		for elem in room.getParticipants():
			if elem==message[24:]:
				return "that nick is already in use"
		room.setNick(message[24:])
		return #nothing more needs to be done.

	elif message[:12]=="load module " and message[12:]: #prevent trying to load an empty module
		result=aihandler.setAID(uid,message[12:]) #fixme: security?
		if result==0:
			reply="success!"
		elif result==1:
			reply="no such module"
	else:
		if type(sre.match('(what\'s|what is) your behaviour\?$',message)) != types.NoneType: #sre.match() matches a regexp to the beginning of a string. because of the $ at the end of our regexp this means we only get a match if the entire string exactly matches it.
			return room.getBehaviour(asstring=True)


	if not reply:
		reply=handleProtection(message)
		if not reply:
			reply=handleReactions(message,uid)
			if not reply:
				reply=handleFactoids(message,uid)
				#otheriwse, check for reaction
				if not reply:
					reply=ReactionsDirect.get(message)
					if type(reply) not in types.StringTypes: #ReactionsDirect.get() returns an integer upon error, but we want to ignore errors.
						reply=ReactionsGlobal.get(message)
						#temp:
						if not reply:
							pass
						elif type(reply)==types.IntType: #if error
							reply=None #ignore
						else:
							prepend=None #don't address the sender if it was a global reaction

					#check again because it might have changed in the meanwhile
					if reply:
						reply=mucReplaceString(reply)


	if reply:

		if prepend:
			#pick a random highlighting char:
			n=randint(0,config.Misc.hlchars.__len__()-1)
			hlchar=config.Misc.hlchars[n]
			del n
			reply="%s%s %s"%(prepend,hlchar,reply)

		return reply


def mucReplaceString(message):
	'''this function replaces the message with elements from the dict. if an error occurs (eg.: due to wrong formatting of the message) it is catched and an appropriate message is returned.
this is defined in a seperate function because the same thing (this) is done twice; once in room() and once in mucHighlight().
because mucHighLight() doesn't know the name of the other person (and because of flexibility issues) the replacedictionary is'''

	try:
		return message%_muc_replace_dictionary
	except KeyError, e:
		return '''I was told to say "%s" now but I don't know what to replace %%(%s)s with'''%(message,e[0])
	except StandardError, e:
		return 'I was taught to say "%s" now, but there seems to be something wrong with that..'%message








def handleFactoids(message,uid):
	'''use this function to check if a message is meant to do something with factoids (change one, add one, etc).'''

	reply=None

	#fetch factoid

	if message[:8].lower()=="what is ":
		reply = Factoids.get(filters.stripQM(message[8:]))
	elif message[:7].lower()=="what's ":
		reply = Factoids.get(filters.stripQM(message[7:]))
	elif message[:17].lower()=="do you know what " and message.strip("?")[-3:]==" is":
		reply = Factoids.get(message[17:-3])
	if type(reply) == types.IntType:
		if reply==1:
			reply="Idk.. can you tell me?"
		elif reply==2:
			reply="whoops... db error :s"
		else: #unspecified error
			reply="an error ocurred"


	if reply: #if there already is a reply
		pass #don't even bother checking all this stuff

	elif message[-1:]=="?":
		reply = Factoids.get(message[:-1])
		if type(reply)==types.IntType:
			reply=None

	#forget factoid
	elif message[:7].lower()=="forget ":
		object=message[7:]
		if object[:5].lower()=="what " and object[-3:]==" is":
			object=object[5:-3]
		result = Factoids.delete(object)
		if result==0:
			reply="k."
		elif result==1:
			reply="I don't know what %s is"%object
		elif result==2:
			reply="woops... database error."
		elif result==3:
			reply="srry, protected factoid. only an admin can delete that."


	#add factoid
	elif ' is ' in message:
		(object,definition)=[elem.strip() for elem in message.split(" is ",1)]
		if uidIsAllowedTo(uid,'protect'):

			result=None
			if definition=="protected":
				result=Factoids.protect(object)
			elif definition in ('public','unprotected'):
				result=Factoids.unProtect(object)
			#fixme: this means you will get the same answer no matter if you protect or unprotect. I don't care, but it could be done nicer.
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
			elif type(result) in types.StringTypes: #means that result holds the definition of the object and not an error code
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


	if message[:3].lower()=="is " and message[-11:]==" protected?":
		message=message[3:-11]

		#check if we're requesting for protectedness of a reaction:
		dunno="I don't know what to say to that anyway..."
		if message[:12].lower()=="reaction to ":
			isprotected=ReactionsGlobal.isProtected(message[12:])
		elif message[:16].lower()=="the reaction to ":
			isprotected=ReactionsGlobal.isProtected(message[16:])

		#and if not requesting for reactions, assume factoid:
		else:
			if message[:8].lower()=="factoid ":
				message=message[8:]
			isprotected=Factoids.isProtected(message)
			dunno="I don't even know what %s is..."%message

		#handle the return values (they are the same for factoids and reactions):
		if isprotected==0:
			return "no"
		elif isprotected==1:
			return "yes"
		elif isprotected==2:
			return "ah crap, a database error"
		elif isprotected==3:
			return dunno
	else:
		return None




def handleReactions(message,uid):
	'''same as handleFactoids, except this one is for reactions. it doesn't fetch em though! only for adding/deleting em.'''

	reply=None

	#if there's " is " in the message, do more checking.
	if " is " in message:



		def _IS(message,direct):
			'''this function is called internally by handleReactions(). if globalordirect is False, global is assumed. if True: direct.'''

			(listenfor,reaction)=[elem.strip() for elem in message.split(" is ",1)]

			if uidIsAllowedTo(uid,'protect'):

				result=None

				if reaction =="protected":
					result=ReactionsGlobal.protect(listenfor)
				elif reaction in ('public','unprotected'):
					result=ReactionsGlobal.unProtect(listenfor)
				#fixme: this means you will get the same answer no matter if you protect or unprotect. I don't care, but it could be done nicer.
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

			#by creating a compatible reference with the same name for both situations we can use one block of code to do two things, depending on the situation.
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
			elif type(result) in types.StringTypes: #means that result holds the definition of the object and not an error code
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




def invitedToMuc(room,situation,by=None,reason=None):
	'''handler to call if invited to a muc room. takes the instance of the (unjoined room), the situation we are in and the reason for the invitation.
situations:
0) already active in room: return an excuse message to the room
1) room known, but inactive: join it and say thx 4 inviting
2) room unknown: create it, join it and say thx'''

	if not type(by)==types.InstanceType:
		by==xmpp.JID(by)

	if not situation:
		if reason:
			room.send("I was invited to this room, being told: %s, but I'm already in here..."%reason)
		else:
			room.send("I was invited to this room for no appearant reason, but I'm already in here...")
	elif situation==1 and by:
		room.join()
		room.send("hey guys =] . thanks for inviting me here again, %s"%by.getNode())
	else:
		room.join()
		room.send("hi, thx for inviting me here.")






# a directory representing the different behaviour-levels and their textual representations
behaviour={
0:'silent',# with this behaviour you should typically not say anything
1:'shy'   ,# only talk when talked to
2:'normal',# react to everything you can react to, even if not addressed
3:'loud'   # say random things at random moments, be annoying
}

def getBehaviourID(text):
	'''get the numerical ID of the specified behaviour'''
	result=None
	for elem in behaviour.iteritems():
		if elem[1]==text:
			result=elem[0]
			break
	return result