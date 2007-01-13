# coding: utf-8

'''
use this plugin to check if a message is meant to do something
with factoids (change one, add one, etc).
'''

import types

import plugins.factoids_internal as Factoids
from user_identification import isAllowedTo as uidIsAllowedTo


def process( identity, originalMessage, originalReply ):

	message = originalMessage
	uid = identity.getUid()
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
		(object, definition) = [elem.strip() for elem in message.split(" is ",1)]
		if uidIsAllowedTo( uid, 'protect' ):

			result = None
			if definition == "protected":
				result = Factoids.protect(object)
			elif definition in ('public','unprotected'):
				result = Factoids.unProtect(object)
			#TODO: this means you will get the same answer no matter if you
			#protect or unprotect. I don't care, but it could be done nicer.
			if result == None:
				pass
			elif result == 0:
				reply="k"
			elif result == 1:
				reply="I don't know what that means"
			elif result == 2:
				reply="ah crap crap crap... database error!"
			elif result == 3:
				reply = "yeah, I know.."
			else: #unspecified error messages
				reply = "hmm.. error."


		if not reply:
			result = Factoids.get(object)
			if result == 1: # object is not known yet
				Factoids.add(object,definition,uid)
				reply = "k"
			elif result == 2:
				reply = "oh noes, a database error!"
			elif type( result ) in types.StringTypes:
				#the result holds an error code
				if result == definition:
					reply = "I know"
				else:
					reply = "but... but... %s is %s" % (object, result)

	if reply:
		return (originalMessage, reply)
	else:
		return (originalMessage, originalReply)
