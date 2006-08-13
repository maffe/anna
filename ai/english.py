# -- coding: utf-8 --
'''english localisation for anna'''

from random import randint
import sre
import types


#fixme: this importing is all quite a mess..

import factoids_reactions
Factoids=factoids_reactions.Factoids()
Reactions=factoids_reactions.Reactions()

import misc
admin=misc.Admin()
filters=misc.StringFilters()
import stats
import config
import plugin


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

	#admin stuff
	if identity.isAllowedTo('stop') and message=="stop":
		#pm.send(identity,"ok, well, I'm leaving...") #fixme: we need a nice and clean solution for this that fits the idea! what about returning a message, waiting till it is delivered and stopping only after that?
		admin.stop(nocheck=True) #only admins get here so no need to check again

	if identity.isAllowedTo('protect') and message[:8]=="protect ":
		message=message[8:]
		if message[:16]=="the reaction to ":
			reply = Reactions.protect(message[16:],silent=False)
		elif message[:12]=="reaction to ":
			reply = Reactions.protect(message[12:],silent=False)
		elif message[:8]=="factoid ":
			reply = Factoids.protect(message[8:],silent=False)
		else:
			reply = Factoids.protect(message,silent=False)


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

	if not reply:
		reply=handleProtection(message)
	if not reply:
		reply=handleReactions(message,uid)
	if not reply:
		reply=handleFactoids(message,uid)
	#otheriwse, check for reaction
	if not reply:
		reply = Reactions.get(message,True)

	if reply:
		identity.send(reply)




def room(message,sender,typ,room):
	'''use this function to get yourself a reply that fits a mutli user chat message.

- if the message starts with the current nickname followed by a highlighting character, handle it as a direct message (just like PM) through self.direct()
- check if someone asked for a factoid, by filtering "what is", "?", etc.
- finally, if all else failed, check if there's a reaction connected to this message
- if any of the above gave a result by setting the "message" variable, send that very variable back to the room with muc.send()'''



	nickname = room.nick

	if sender.lower()==nickname.lower():
		return False  #prevent loops

	#body and message are used totally in the wrong way. for historical reasons ( ;] ) the body variable still exists, and message holds the reply. this should change to message holding the incoming message and reply holding the reply.
	message=filters.xstrip(message)
	reply=''



	#handle messages with leading nick as direct messages
	nick_len = nickname.__len__()+1
	for elem in config.Misc.hlchars:
		# Check if we have nickanme + one hlchars
		if message.lower()[:nick_len]==nickname+elem:
			reply=mucHighlight(message[nick_len:].strip(),room,prepend=sender)


	if reply: #if reply is set, skip the checks.
		pass


	#get factoid
	elif message.lower()[:8]=="what is ":
		reply=Factoids.get(message[8:],silent=True)
	elif message.lower()[:7]=="what's " :
		reply=Factoids.get(message[7:],silent=True)
	elif message[-1:]=="?":
		reply=Factoids.get(message[:-1],silent=True)




	else:
		reply=Reactions.get(message,True,user=sender)


	if reply and room.getBehaviour(asstring=False): #if silent: don't speak
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
		try:
			room.setBehaviour(message[4:])
			return 'k.'
		except ValueError, e:
			return e.__str__()
	else:
		if type(sre.match('(what\'s|what is) your behaviour\?$',message)) != types.NoneType:
			return room.getBehaviour(asstring=True)


	if not reply:
		reply=handleProtection(message)
	if not reply:
		reply=handleReactions(message,uid)
	if not reply:
		reply=handleFactoids(message,uid)
	#otheriwse, check for reaction
	if not reply:
		reply = Reactions.get(message,True)


	if prepend and reply:
		#pick a random highlighting char:
		n=randint(0,config.Misc.hlchars.__len__()-1)
		hlchar=config.Misc.hlchars[n]
		del n
		reply="%s%s %s"%(prepend,hlchar,reply.decode('utf-8','replace'))

	try:
		return reply
	except AttributeError:
		return None




def handleFactoids(message,uid):
	'''use this function to check if a message is meant to do something with factoids (change one, add one, etc).'''

	#fetch factoid
	if message[:8].lower()=="what is ":
		reply = Factoids.get(message[8:],silent=False)
	elif message[:7].lower()=="what's ":
		reply = Factoids.get(message[7:],silent=False)
	elif message[:17].lower()=="do you know what " and message.strip("?")[-3:]==" is":
		reply = Factoids.get(message[17:-3],silent=False)
	elif message[-1:]=="?":
		reply = Factoids.get(message[:-1],silent=True)

	#forget factoid
	elif message[:7].lower()=="forget ":
		message=message[7:]
		if message[:5].lower()=="what " and message[-3:]==" is":
			reply = Factoids.delete(message[5:-3])
		else:
			reply = Factoids.delete(message)


	#add factoid
	elif ' is ' in message:
		(object,definition)=[elem.strip() for elem in message.split(" is ",1)]
		if definition =="protected":
			reply=Factoids.protect(object)
		elif definition in ('public','unprotected'):
			reply=Factoids.unProtect(object)
		else:
			reply = Factoids.add(object,definition,uid)

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
			isprotected=Reactions.isProtected(message[12:])
		elif message[:16].lower()=="the reaction to ":
			isprotected=Reactions.isProtected(message[16:])

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
			return dunno
	else:
		return None


def handleReactions(message,uid):
	'''same as handleFactoids, except this one is for reactions. it doesn't fetch em though! only for adding/deleting em.'''
						### GLOBAL REACTIONS ####

	#add global reaction
	if message[:12].lower()=="reaction to " and " is " in message[12:]:
		(listenfor,reaction)=[elem.strip() for elem in message[12:].split(" is ",1)]
		if reaction =="protected":
			reply=Reactions.protect(listenfor)
		elif reaction in ('public','unprotected'):
			reply=Reactions.unProtect(listenfor)
		else:
			reply = Reactions.add(listenfor,reaction,uid)

	#del global reaction
	elif message[:19].lower()=="forget reaction to ":
		reply = Reactions.delete(message[19:])

	try:
		return reply
	except NameError:
		return None




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