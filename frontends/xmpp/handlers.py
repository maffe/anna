# -- coding: utf-8 --
'''Define the handlers'''

import xmpp
import types

import misc
admin=misc.Admin()
import stringfilters as filters
import user_identification as uids
import frontends.xmpp as xmpp_frontend
import rooms

import aihandler

#xmpppy connection object.
#conn = 

def pm( conn, mess ):
	"""handler that deals with messages directed directly to the bot by PM."""


	message = mess.getBody()
	jid     = mess.getFrom()
	#ignore empty and overloaded messages
	if not message or message.__len__() > 255:
		return False

	#create a Private Message instance
	pm = xmpp_frontend.PM( jid, conn )

	# prepare some variables


	#check if this is a direct pm or a pm through a muc room
	if rooms.isActive( jid, 'xmpp' ):
		counterpart = jid.getResource() #the name of the person we're talking with
	else:
		# if the room is either known but not active, or not known at all, this is
		#to be assumed to be a direct PM:
		counterpart = jid.getNode()

	if admin.isAdmin( jid.getStripped() ):
		permissions = ['all']
	else:
		permissions = []

	counterpart = xmpp_frontend.PM( jid, nick = counterpart, permissions = permissions )


	if message[:10] == "send raw: " and counterpart.isAllowedTo('send_raw'):
		#this is solely jabber-related, so it belongs here.
		conn.send( message[10:] )
		return 'k.'

	else:
		#to get our AIModule we first check if this uid already has a certain ai module in use.
		aimodule = aihandler.getAIReferenceByUID( counterpart.getUid() )
		#if there was an error aimodule is now types.IntType
		if type( aimodule ) == types.IntType:
			#in that case we just force the chat.english ai module
			aimodule = aihandler.getAIReferenceByAID( 'chat_english' )
			if type( aimodule ) == types.IntType:
				sys.exit( 'default AI module ai/chat_english.py wasnt found.' )
		return aimodule.direct( message, counterpart, typ = 'xmpp' )





def muc( conn, mess ):
	'''handler for multi user chitchat messages =D hurray.'''


	message = mess.getBody()
	#stop if this is a delayed message or if there is no content
	if not message or mess.getProperties().count( xmpp.NS_DELAY ):
		return False

	jid  = mess.getFrom().getStripped()
	user = mess.getFrom().getResource() # the sender of the message

	if not user:
		#<message type='groupchat' /> without resource
		return False
		#messages from groupchats are not interesting

	#copy or create an instance. there could be a weird situation where a
	#message is received from a groupchat that isn't registered yet (not
	#expected, but it COULD happen). in that case: create a new room instance
	try:
		room = rooms.get( jid, 'xmpp' )
	except ValueError:
		room = rooms.new( jid, 'xmpp' )



	#load the aimodule the same way as in direct()
	aimodule = aihandler.getAIReferenceByUID( room.getUid() )
	if type(aimodule) == types.IntType: #if error:
		aimodule = aihandler.getAIReferenceByAID('chat_english')
		if type(aimodule) == types.IntType:
			sys.exit( "default AI module <chat_english> not found." )

	return aimodule.room( message, sender = user, typ = 'xmpp', room = room )


def joinmuc( conn, mess ):
	"""handle invitation to a muc.
three possible situations:
0) already active in room: return an excuse message to the room
1) room known, but inactive: join it and say thx 4 inviting
2) room unknown: create it, join it and say thx

if not 2, get the existing instance, otherwise create a new one. pass this on to the ai module and have that handle delivering messages etc. not that it is up to the ai module to actually join! this gives the opportunity to tweak the instance before joining the room."""

	jid    = mess.getFrom()
	by     = xmpp.JID( mess.getTag( 'x' ).getTag( 'invite' ).getAttr( 'from' ) )
	reason = mess.getTag( 'x' ).getTag( 'invite' ).getTagData( 'reason' )

	if rooms.isActive( jid, 'xmpp' ):
		situation = 0
		room = rooms.get( jid, 'xmpp' )
	elif rooms.exists( jid, 'xmpp' ):
		situation = 1
		room = rooms.get( jid, 'xmpp' )
		room.join()
	else:
		situation = 2
		room = rooms.new( jid, 'xmpp' )
		room.join()

	#load the aimodule the same way as in direct()
	aimodule = aihandler.getAIReferenceByUID( room.getUid() )
	if type( aimodule ) == types.IntType:
		aimodule = aihandler.getAIReferenceByAID( 'chat_english' )
		if type( aimodule ) == types.IntType:
			sys.exit( 'default AI module <chat_english> not found.' )

	aimodule.invitedToMuc( room, situation, by, reason )




def presence( conn, presence ):
	'''handle <presence/>.
return False if type attribute == 'error'.'''

	presencetype = presence.getType()
	if presencetype == "error":
		return False

	x = presence.getTag( 'x' )
	try:
		ns = x.getNamespace()
	except AttributeError:
		return False

	jid = presence.getFrom()

	if ns == xmpp.NS_MUC_USER:

		#get the instance of the room (create one if there ain't none yet)
		room = rooms.exists(jid, "xmpp") and rooms.get(jid, "xmpp") or rooms.new(jid, "xmpp")
		nick = jid.getResource()

		#if it was a 'leave presence', remove the participant
		if presencetype == 'unavailable':
			try:
				room.delParticipant( nick )
			except KeyError:
				pass
		else:
			item        = x.T.item
			role        = item.getAttr('role')
			jid         = item.getAttr('jid')
			participant = xmpp_frontend.MUCParticipant( nick, presence, role, jid )
			room.addParticipant( participant )



def subscribtion( conn, presence ):
	'''Handle <presence type='subscribe' />.

We don't (actively) keep all users in the roster too. First of all;
because this is just the jabber front-end to the actual AI module.
If we relied on the roster it would make the whole code xmpp-dependant.
Second; there's no use of keeping them all in the roster if we're
gonna keep them all in our own database too anyway (uids).

Only subscription matters: we allow the other to see the status and add this JID to his roster.

http://www.ietf.org/rfc/rfc3921.txt chapter 8'''

	reply = xmpp.Presence( to = presence.getFrom(), typ = 'subscribed', xmlns = None )
	conn.send( reply )




def version_request( conn, iq ):
	'''respond to a version info request. of course, this is a #fixme; we should check .svn/entries for the current revision instead of returning 666.'''
	reply = iq.buildReply( 'result' )
	#add <name/> and <version/> in accordance with JEP-0092
	reply.T.query.addChild( name = 'name',    payload = ['Anna'] )
	reply.T.query.addChild( name = 'version', payload = ['666'] )

	conn.send( reply )
