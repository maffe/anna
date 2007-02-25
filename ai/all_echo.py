"""Your average echo module.

Functional but not very useful: replies to all incoming messages by echoing
the message. Useful for testing.

"""
import aihandler

def direct(message, identity, typ):
	"""Echo the incoming message."""

	if message.startswith("load module ") and message[12:]:
		result = aihandler.setAID(identity.getUid(),message[12:])
		if result == 0:
			message="success!"
		elif result == 1:
			message="no such module"


	identity.send(message)

def room(message, sender, room):
	"""Echo the incoming group message back to the room."""

	if sender.getNick().lower() == room.getNick().lower():
		return False

	if message.startswith("load module ") and message[12:]:
		result = aihandler.setAID(room.getUid(), message[12:])
		if result == 0:
			message = "success!"
		elif result == 1:
			message = "no such module"

	room.send(message)
