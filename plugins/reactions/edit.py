"""Functions that allow *editing* of reactions, NOT fetching."""
#TODO: this whole module needs a review

import mysql
from plugins.reactions import Internals
i_direct = Internals()
i_global = Internals()
i_direct.TABLE_NAME = "reactions_direct"
i_global.TABLE_NAME = "reactions_global"
from user_identification import isAllowedTo as uidIsAllowedTo

def process(identity, message, originalReply):
	"""Check if this message wants to modify/create/etc a reaction."""
	uid = identity.getUid()
	reply = None

	#if there's " is " in the message, do more checking.
	if " is " in message:

		#determine whether it's a global or direct reaction:
		if message[:12].lower() == "reaction to ":
			reply = is_(message[12:], True, uid)
		elif message[:19].lower() == "direct reaction to ":
			reply = is_(message[19:], True, uid)
		elif message[:19].lower() == "global reaction to ":
			reply = is_(message[19:], False, uid)

	if not reply and message[:7].lower() == "forget ":

		#del global reaction
		if message[:19].lower() == "forget reaction to ":
			reply = delete(message[19:], True)
		elif message[:26].lower() == "forget direct reaction to ":
			reply = delete(message[26:],True)
		elif message[:26].lower() == "forget global reaction to ":
			reply = delete(message[26:], False)
	
	return (message, reply or originalReply)

def delete(listen_for, direct):
	"""Delete a reaction."""
	if direct:
		result = i_direct.delete(listen_for)
	else:
		result = i_global.delete(listen_for)

	if result == 0:
		return "k"
	elif result == 1:
		return "I don't know what that means anyway"
	elif result == 2:
		return "shit, db error."
	elif result == 3:
		return "That factoid is protected."

def is_(message, direct, uid):
	"""This function is called when the message contains " is " and
	defines a reaction. If direct is False, global is assumed. if True:
	direct."""
	#TODO: this is an ugly way of handling these messages.

	# By creating a compatible reference with the same name for both situations
	# we can use one block of code to do two things, depending on the situation.
	internals = direct and i_direct or i_global

	(listenfor, reaction) = [elem.strip() for elem in message.split(" is ", 1)]

	if uidIsAllowedTo(uid, 'protect'):

		result = None

		if reaction == "protected":
			result = internals.protect(listenfor)
		elif reaction in ('public', 'unprotected'):
			result = internals.unProtect(listenfor)
		#TODO: this means you will get the same answer no matter if
		#you protect or unprotect. I don't care, but it could be done nicer.
		if result is None:
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

	if reaction.endswith(" and append a questionmark"):
		reaction = ''.join(reaction[:-26], '?')

	result = internals.get(listenfor)
	if result == 1: # object is not known yet
		internals.add(listenfor, reaction, uid)
		return "k"
	elif result == 2:
		return "oh noes, a database error!"
	elif isinstance(result, basestring):
		#means that result holds the definition of the object and
		#not an error code
		if result == reaction:
			return "I know"
		else:
			return "but the reaction to %s is %s" % (listenfor, result)
	else: #an unspecified error occured:
		return "uhh... error?"
