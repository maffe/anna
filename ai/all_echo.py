# -- coding: utf-8 --

"""your average echo module. functional but not very useful."""

import aihandler

def direct(message,identity,typ):
	"""echo the incoming message"""

	if message[:12]=="load module " and message[12:]: #prevent trying to load an empty module
		result=aihandler.setAID(identity.getUid(),message[12:]) #fixme: security?
		if result==0:
			message="success!"
		elif result==1:
			message="no such module"


	identity.send(message)

def room(message,sender,typ,room):
	"""echo the incoming group message back to the room"""

	if sender.lower()== room.getNick().lower():
		return False  #prevent loops

	if message[:12]=="load module " and message[12:]: #prevent trying to load an empty module
		result=aihandler.setAID(room.getUid(),message[12:]) #fixme: security?
		if result==0:
			message="success!"
		elif result==1:
			message="no such module"

	room.send(message)