# -- coding: utf-8 --

'''ai/theenglishnazigame.py

this file is the english AI module for thenazigame.'''

import aihandler


def direct(message,identity,typ):
	'''handle a direct message'''

	if message[:12]=="load module " and message[12:]: #prevent trying to load an empty module
		result=aihandler.setAID(identity.getUid(),message[12:]) #fixme: security?
		if result==0:
			reply="success!"
		else:
			reply="sorry, failed."



	identity.send(reply)

def room(message,sender,typ,room):
	'''handle a message from a groupchat'''
	room.send('sorry, but the thenazigame module currently only works in private conversations.\nloading the chat_english module.')
	aihandler.setAID(room.getUid(),'chat_english')