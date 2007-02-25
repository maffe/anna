"""Use this plugin to check if a message is meant to do something
with factoids (change one, add one, etc).

NOT for fetching them.

"""
import plugins.factoids_internal as internals
from user_identification import isAllowedTo as uidIsAllowedTo

def process(identity, message, reply):
	"""Parse a messsage for expected syntax.

	If not reply is None, this module will exit right away. This is to prevent
	the module from parsing messages meant for other modules.
	
	"""
	if not reply is None:
		return (message, reply)

	uid = identity.getUid()

	#forget factoid
	if message[:7].lower() == "forget ":
		object = message[7:]
		if object.startswith("what ") and object.endswith(" is"):
			object = object[5:-3]
		result = internals.delete(object)
		if result == 0:
			return (message, "k.")
		elif result == 1:
			return (message, "I don't know what %s is" % object)
		elif result == 2:
			return (message, "woops... database error.")
		elif result == 3:
			return (message, "srry, protected factoid. only an admin can delete that.")

	#add factoid
	if not " is " in message:
		return (message, reply)

	(object, definition) = [elem.strip() for elem in message.split(" is ", 1)]
	if uidIsAllowedTo(uid, "protect"):

		result = None
		if definition == "protected":
			result = internals.protect(object)
		elif definition in ("public", "unprotected"):
			result = internals.unProtect(object)
		#TODO: this means you will get the same answer no matter if you
		#protect or unprotect. I don't care, but it could be done nicer.
		if result == None:
			pass
		elif result == 0:
			return (message, "k")
		elif result == 1:
			return (message, "I don't know what that means")
		elif result == 2:
			return (message, "ah crap crap crap... database error!")
		elif result == 3:
			return (message, "yeah, I know..")
		else: #unspecified error messages
			return (message, "hmm.. error.")


	result = internals.get(object)
	if result == 1: # object is not known yet
		internals.add(object, definition, uid)
		return (message, "k")
	elif result == 2:
		return (message, "oh noes, a database error!")
	elif isinstance(result, basestring):
		if result == definition:
			return (message, "I know")
		else:
			return (message, "but... but... %s is %s" % (object, result))

	return (message, ''.join("DEBUG: hi, you found a bug in the code. Could you",
		" please tell bb@jabber.xs4all.nl about this? Kthx!"))
