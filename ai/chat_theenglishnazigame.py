# -- coding: utf-8 --

'''ai/theenglishnazigame.py

this file is the english AI module for thenazigame.'''

import aihandler


def direct(message,identity,typ):
	'''handle a direct message'''

	if message[:12]=="load module " and message[12:]: #prevent trying to load an empty module
		result=aihandler.setAID(uid,message[12:]) #fixme: security?
		if result==0:
			reply="success!"
	else:
		reply="yup, thenazigame module loaded!"

	identity.send(reply)
