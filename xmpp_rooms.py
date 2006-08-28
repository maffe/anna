# -- coding: utf-8 --
'''use these functions to handle the whole collection of MUC-rooms known to us'''

import types


import config
from xmpp_abstract import MUC


def join(jid,conn):
	'''join a muc room. use the existing instance if available, create a new one if not.
note: if you want more flexible joining (for example; setting autojoin to False, chaging some values before joining, etcetera), you can do this instead:
- create the new room with new() first
- get the instance of the new room with self.getByJid()
- suit that instance to fit your needs
- use its join() method to finally join the room'''
	try:
		room=getByJid(jid)
		message=room.join(silent=False)
	except ValueError:
		result=new(jid,conn)
		#if the above succeeded, result should now be an instance of the room that was joined
		if type(result)==types.InstanceType:
			message="k."
		else:
			message="ehmm... error?"
	return message


def new(jid,conn):
	'''add a room with a specified jid to the list. return its instance.'''
	if isExistant(jid):
		if silent:
			return False
	newroom=MUC(jid,conn,autojoin=False)
	config.Misc.rooms.append(newroom)
	return newroom


def remove(jid):
	'''remove a room with this jid from the list. uses getByJid() but does not catch exceptions.'''
	room=getByJid(jid)

	config.Misc.rooms.remove(room)
	return room.leave()


def getActive():
	'''return an iterable object with all instances of rooms that are active (also look at self.getAll() )'''
	result=()
	for elem in config.Misc.rooms:
		if elem.isActive():
			result+=(elem,)
	return result


def getAll():
	'''return an iterable object with all instances of the known rooms (you will generally want to use self.getActive() )'''
	result=()
	for elem in config.Misc.rooms:
		result+=(elem,)
	return result


def getByJid(jid):
	'''return the room instance by providing it's jid (xmpp.JID() instance or string). raises a ValueError if not found.'''
	for elem in config.Misc.rooms:
		if elem.getJid().bareMatch(jid):
			return elem
	#if we get up to here, there is no such room
	raise ValueError, 'no room with jid "%s"'%jid


def isExistant(jid):
	'''return True if a specified jid is known to us as a muc room, return False if it isn't (similar to getByJid(), but not entirely the same)'''
	for elem in config.Misc.rooms:
		if elem.getJid().bareMatch(jid):
			return True
	return False


def isActive(jid):
	'''similar to self.isExistant(), but slightly different: only return True (bool) if the room is not only known but also active'''
	for elem in config.Misc.rooms:
		if elem.getJid().bareMatch(jid) and elem.isActive():
			return True
	return False