# -- coding: utf-8 --
"""Define the handlers"""

import xmpp
import sys

import admin
import stringfilters as filters
import user_identification as uids
import frontends.xmpp as xmpp_frontend
import rooms
import aihandler

def pm(conn, mess):
	"""Handler that deals with messages directed directly to the bot by PM."""

	message = mess.getBody()
	jid     = mess.getFrom()
	# Ignore empty and overloaded messages.
	if not message or len(message) > 255:
		return False

	# Create a Private Message instance.
	pm = xmpp_frontend.PM(jid, conn)

	# Check if this is a direct pm or a pm through a muc room.
	if rooms.isActive(jid, 'xmpp'):
		counterpart = jid.getResource() # The name of the person we're talking with
	else:
		# If the room is either known but not active, or not known at all, this is
		# to be assumed to be a direct PM:
		counterpart = jid.getNode()

	counterpart = xmpp_frontend.PM(jid, nick = counterpart)

	if message[:10] == "send raw: " and counterpart.isAllowedTo('send_raw'):
		#this is solely jabber-related, so it belongs here.
		conn.send(message[10:])
		return 'k.'

	else:
		# To get our AIModule we first check if this uid already has a certain ai
		# module in use.
		aimodule = aihandler.getAIReferenceByUID(counterpart.getUid())
		# If there was an error aimodule is now an integer.
		if isinstance(aimodule, int):
			#In that case we just force the annai ai module.
			aimodule = aihandler.getAIReferenceByAID('annai')
			if isinstance(aimodule, int):
				sys.exit('default AI module ai/annai.py wasnt found.')
		return aimodule.direct(message, counterpart)

def muc(conn, mess):
	"""Handler for multi user chitchat messages."""

	message = mess.getBody()
	# Stop if this is a delayed message or if there is no content.
	if not message or mess.getProperties().count(xmpp.NS_DELAY):
		return False

	jid = mess.getFrom().getStripped()

	# Copy or create an instance. there could be a weird situation where a
	# message is received from a groupchat that isn't registered yet (not
	# expected, but it COULD happen). in that case: create a new room instance.
	try:
		room = rooms.get(jid, 'xmpp')
	except ValueError:
		room = rooms.new(jid, 'xmpp')

	senderNick = mess.getFrom().getResource()

	if not senderNick:
		# Messages from groupchats are not interesting.
		return False

	sender = xmpp_frontend.MUCParticipant(room, senderNick)

	# Load the aimodule the same way as in direct().
	aimodule = aihandler.getAIReferenceByUID(room.getUid())
	if isinstance(aimodule, int): #if error:
		aimodule = aihandler.getAIReferenceByAID('annai')
		if isinstance(aimodule, int):
			sys.exit("default AI module <annai> not found.")

	return aimodule.room(message, sender, room)

def joinmuc(conn, mess):
	"""Handle invitation to a muc.

	Three possible situations:
	0) already active in room: return an excuse message to the room
	1) room known, but inactive: join it and say thx 4 inviting
	2) room unknown: create it, join it and say thx

	If not 2, get the existing instance, otherwise create a new one. Pass this
	on to the ai module and have that handle delivering messages etc. Not that
	it is up to the ai module to actually join! This gives the opportunity to
	tweak the instance before joining the room.
	
	"""
	jid    = mess.getFrom()
	by     = xmpp.JID(mess.getTag('x').getTag('invite').getAttr('from'))
	by     = by.getStripped()
	reason = mess.getTag('x').getTag('invite').getTagData('reason')

	if rooms.isActive(jid, 'xmpp'):
		situation = 0
		room = rooms.get(jid, 'xmpp')
	elif rooms.exists(jid, 'xmpp'):
		situation = 1
		room = rooms.get(jid, 'xmpp')
		room.join()
	else:
		situation = 2
		room = rooms.new(jid, 'xmpp')
		room.join()

	# TODO: this requires a more elegant fall-back (no hard-coded "annai").
	# Load the aimodule the same way as in direct()
	aimodule = aihandler.getAIReferenceByUID(room.getUid())
	if isinstance(aimodule, int):
		aimodule = aihandler.getAIReferenceByAID('annai')
		if isinstance(aimodule, int):
			sys.exit('default AI module <annai> not found.')

	aimodule.invitedToMuc(room, situation, by, reason)

def presence(conn, presence):
	"""Handle <presence/> tags.

	Return False if type attribute == 'error'.
	
	"""
	presencetype = presence.getType()
	if presencetype == "error":
		return False

	x = presence.getTag('x')
	try:
		ns = x.getNamespace()
	except AttributeError:
		return False

	jid = presence.getFrom()

	if ns == xmpp.NS_MUC_USER:

		roomjid = xmpp.JID(jid.getStripped())

		#get the instance of the room (create one if there ain't none yet)
		room = (rooms.exists(roomjid, "xmpp")
			and rooms.get(roomjid, "xmpp")
			or  rooms.new(roomjid, "xmpp"))

		nick  = jid.getResource()
		item  = x.T.item
		#role  = item.getAttr("role")
		#jid   = item.getAttr("jid")

		if presencetype != "unavailable":
			participant = xmpp_frontend.MUCParticipant(nick, presence)#, role, jid)
			room.addParticipant(participant)
			return

		else:
			try:
				if nick == room.getNick() and x.T.status.getAttr("code") == "303":
					#the bot's nick got changed
					room.setNick(item.getAttr('nick'))
					return
			except AttributeError:
				#<item/> has no <status/> child
				pass

			try:
				#if it was a 'leave presence', remove the participant
				room.delParticipant(nick)
			except KeyError:
				pass

def subscribtion(conn, presence):
	"""Handle <presence type='subscribe' />.

	We don't (actively) keep all users in the roster too. First of all;
	because this is just the jabber front-end to the actual AI module.
	If we relied on the roster it would make the whole code xmpp-dependant.
	Second; there's no use of keeping them all in the roster if we're
	gonna keep them all in our own database too anyway (uids).

	Only subscription matters: we allow the other to see the status and
	add this JID to his roster.

	http://www.ietf.org/rfc/rfc3921.txt chapter 8"""

	reply = xmpp.Presence(
		to = presence.getFrom(),
		typ = 'subscribed',
		xmlns = None
	)
	conn.send(reply)

def version_request(conn, iq):
	"""Respond to a version info request.
	TODO: It would be nice to return the revision number in the version
	tag instead of just "svn"."""
	reply = iq.buildReply('result')
	#add <name/> and <version/> in accordance with JEP-0092
	reply.T.query.addChild(name = 'name', payload = ['Anna'])
	reply.T.query.addChild(name = 'version', payload = ['svn'])

	conn.send(reply)
