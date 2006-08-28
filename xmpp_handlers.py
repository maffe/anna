# -- coding: utf-8 --
'''
handlers.py
///////////////////////////////////////
Define the handlers
///////////////////////////////////////
'''

import xmpp
import types

import misc
admin=misc.Admin()
import stringfilters as filters
import user_identification as uids
import xmpp_abstract
import xmpp_rooms as rooms

import aihandler


def pm(conn,mess):
	"""handler that deals with messages directed directly to the bot by PM."""


	message=mess.getBody()
	jid=mess.getFrom()
	#prevent overloaded messages
	if not message or message.__len__()>255:
		return False
	pm=xmpp_abstract.PM(jid,conn)

	# prepare some variables


	#check if this is a direct pm or a pm through a muc room
	if rooms.isActive(jid):
		counterpart=jid.getResource() #the name of the person we're talking with
	else: # if the room is either known but not active, or not known at all, this is to be assumed to be a direct PM:
		counterpart=jid.getNode()

	if admin.isAdmin(jid.getStripped()):
		permissions=['all']
	else:
		permissions=[]

	counterpart=xmpp_abstract.PM(jid,conn,nick=counterpart,permissions=permissions)

	#this is a problem. how do we fit this in the new idea of seperating the jabber part and the ai part? for now, I can't think of anything simple.
	if message[:5].lower()=="join ":
		return rooms.join(message[5:],conn)
	elif message[:13].lower()=="please leave ":
		try:
			room=rooms.getByJid(message[13:])
			return room.leave()
		except ValueError:
			return "uhh.. I'm not even in there.."


	if message[:10]=="send raw: " and counterpart.isAllowedTo('send_raw'): #this is solely jabber-related, so it belongs here.
		conn.send(message[10:])
		return 'k.'
	else:
		#to get our AIModule we first check if this uid already has a certain ai module in use.
		aimodule=aihandler.getAIReferenceByUID(counterpart.getUid())
		#if there was an error aimodule is now types.IntType
		if type(aimodule)==types.IntType:
			#in that case we just force the chat.english ai module
			aimodule=aihandler.getAIReferenceByAID('chat_english')
			if type(aimodule)==types.IntType:
				sys.exit('default AI module ai/chat_english.py wasnt found.')
		return aimodule.direct(message,counterpart,typ='jabber')





def muc(conn,mess):
	'''handler for multi user chitchat messages =D hurray.'''


	message=mess.getBody()
	if not message or message.__len__()>255 :
		return False
	if mess.getProperties().count("jabber:x:delay"): #stop if this is a delayed message
		return False

	jid=mess.getFrom()
	user=jid.getResource() # the sender of the message
	if not user: #<message type='groupchat' /> without resource
		return False #IF by horror one finds a room that does not set the nick as resource, a loop cannot be prevented. therefore: ignore. type='groupchat' from rooms aren't interesting anyway, so we don't care (A)
	#copy or create an instance
	try:
		room=rooms.getByJid(jid)
	except ValueError:
		room=rooms.new(jid,conn,autojoin=False)



	#load the aimodule the same way as in self.direct()
	aimodule=aihandler.getAIReferenceByUID(room.getUid())
	if type(aimodule)==types.IntType:
		aimodule=aihandler.getAIReferenceByAID('chat_english')
		if type(aimodule)==types.IntType:
			sys.exit('default AI module ai/chat_english.py wasnt found.')

	return aimodule.room(message,sender=user,typ='jabber',room=room)


def joinmuc(conn,mess):
	"""handle invitation to a muc.
three possible situations:
0) already active in room: return an excuse message to the room
1) room known, but inactive: join it and say thx 4 inviting
2) room unknown: create it, join it and say thx

if not 2, get the existing instance, otherwise create a new one. pass this on to the ai module and have that handle delivering messages etc. not that it is up to the ai module to actually join! this gives the opportunity to tweak the instance before joining the room."""

	jid=mess.getFrom()
	by=xmpp.JID(mess.getTag('x').getTag('invite').getAttr('from'))
	reason=mess.getTag('x').getTag('invite').getTagData("reason")
	try:
		room=rooms.getByJid(jid)
	except ValueError: # situation 2
		room=rooms.new(jid,conn)
		situation=2
	else:
		if room.join(): # situation 1
			situation=1
		else: # situation 0
			situation=0
	#fixme: we need a more elegant solution
	aimodule=aihandler.getAIReferenceByAID('chat_english')
	aimodule.invitedToMuc(room,situation,by,reason)


def presence(conn,presence):
	'''handle <presence/>.
return False if type attribute == 'error'. '''

	presencetype=presence.getType()
	if presencetype=="error":
		return False

	x=presence.getTag('x')
	try:
		ns=x.getNamespace()
	except AttributeError:
		return False

	jid=presence.getFrom()

	if ns=='http://jabber.org/protocol/muc#user':

		nick=jid.getResource()

		#get the instance of the room
		try:
			room=rooms.getByJid(jid)
		except ValueError: #if this room doesn't exist already, join it
			#return False # uncomment this to ignore presence messages from unknown rooms instead of joining 'em
			room=rooms.new(jid,conn)

		#if it was a 'leave presence', remove the participant
		if presencetype=='unavailable':
			try:
				room.delParticipant(nick)
			except KeyError:
				pass
		else:
			item=x.T.item
			role=item.getAttr('role')
			jid =item.getAttr('jid')
			participant=xmpp_abstract.MUCParticipant(nick,presence,role,jid)
			room.addParticipant(participant)




def version_request(conn,iq):
	'''respond to a version info request. of course, this is a #fixme; we should check .svn/entries for the current revision instead of returning 666.'''
	reply=iq.buildReply('result')
	#add <name/> and <version/> in accordance with JEP-0092
	reply.T.query.addChild(name='name',payload=['Anna'])
	reply.T.query.addChild(name='version',payload=['666'])
	conn.send(reply)