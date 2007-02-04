# coding: utf-8

"""
Reactions to specified bits of text. For example:
<you> bla
<anna> blabla

 -- Direct Reactions --

A direct reaction is a reaction to something directly addressed to the
chatbot. If the user would just have said "help" in our example, the
reaction would not have been appropriate.

Example:
<user> anna: help
<anna> user: you can define things for me and I will remember them.

 -- Global Reactions --

A global reaction is a reaction to something not directly addressed to the
bot but rather to a remark somebody makes, just like that.

For example:
<user> /me dances *
<anna> /me dances too *

See the wiki for more information: http://0brg.xs4all.nl/anna/wiki/

"""

#TODO: this whole module needs a review

import types

import mysql
from plugins.reactions import internal as ReactionsDirect
ReactionsDirect.TABLE_NAME = "reactions_direct"
from plugins.reactions import internal as ReactionsGlobal
ReactionsGlobal.TABLE_NAME = "reactions_global"
from user_identification import isAllowedTo as uidIsAllowedTo


def process( identity, message, originalReply ):

	uid = identity.getUid()
	reply = None

	#if there's " is " in the message, do more checking.
	if " is " in message:

		#determine whether it's a global or direct reaction:
		if message[:12].lower() == "reaction to ":
			reply = _is( message[12:], True, uid )
		elif message[:19].lower() == "direct reaction to ":
			reply = _is( message[19:], True, uid )
		elif message[:19].lower() == "global reaction to ":
			reply = _is( message[19:], False, uid )


	if not reply and message[:7].lower() == "forget ":

		#del global reaction
		if message[:19].lower() == "forget reaction to ":
			reply = _del( message[19:], True )
		elif message[:26].lower() == "forget direct reaction to ":
			reply = _del( message[26:],True)
		elif message[:26].lower() == "forget global reaction to ":
			reply = _del( message[26:], False )
	
	if reply:
		return (message, reply)
	else:
		return (message, originalReply)


def _del( listen_for, direct ):
	"""Delete a reaction."""
	if direct:
		result = ReactionsDirect.delete( listen_for )
	else:
		result = ReactionsGlobal.delete( listen_for )

	if result == 0:
		return "k"
	elif result == 1:
		return "I don't know what that means anyway"
	elif result == 2:
		return "shit, db error."
	elif result == 3:
		return "that factoid is protected. an admin needs to unprotect it before you can remove it."


def _is( message, direct, uid ):
	"""This function is called when the message contains " is " and
	defines a reaction. If direct is False, global is assumed. if True:
	direct."""
	#TODO: this is an ugly way of handling these messages.

	(listenfor, reaction) = [elem.strip() for elem in message.split( " is ", 1 )]

	if uidIsAllowedTo( uid, 'protect' ):

		result = None

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
		ReactionsClass = ReactionsDirect
	else:
		ReactionsClass = ReactionsGlobal

	result = ReactionsClass.get(listenfor)
	if result == 1: # object is not known yet
		ReactionsClass.add( listenfor, reaction, uid )
		return "k"
	elif result == 2:
		return "oh noes, a database error!"
	elif type( result ) in types.StringTypes:
		#means that result holds the definition of the object and
		#not an error code
		if result == reaction:
			return "I know"
		else:
			return "but the reaction to %s is %s" % (listenfor, result)
	else: #an unspecified error occured:
		return "uhh... error?"
