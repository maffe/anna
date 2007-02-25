# -- coding: utf-8 --
"""Use these functions to handle the whole collection of MUC-rooms known to
us, no matter which type.

TODO: make this module really type-independent. - done?

"""

import types
import sys

import config
import frontendhandler

#here, a dictionary of all muc-rooms, like this:
#rooms = { (identifier, typ): <module> }
rooms = {}
#this dictionary should only be accessed by getters and setters.

def exists(id, typ):
	"""Return True if there is a registered instance of this room."""
	return (id, typ) in rooms

def get(id, typ):
	"""return the room instance by providing it's identifier and type. raises a
	ValueError if not found."""
	try:
		return rooms[(id, typ)]
	except KeyError:
		raise ValueError('no %s room with id <%s>' % (typ, id))

def getActive():
	"""Return an iterable object with all instances of rooms that are active.
	
	Also look at getAll().
	
	"""
	result = []
	for elem in rooms.itervalues():
		if elem.isActive():
			result.append(elem)
	return result

def getAll():
	"""Return an iterable object with all instances of the known rooms.
	
	You will generally want to use getActive().
	
	"""
	return rooms.itervalues()

def isActive(id, typ):
	"""Similar to exists(), but slightly different: only return True (bool) if the
	room is not only known but also active."""
	return (id, typ) in rooms and rooms[(id, typ)].isActive()
	#returns False instead of raising KeyError on non-existant room.

def join(id, typ):
	"""Join a muc room.
	
	Use the existing instance if available, create a new one if not.  Note: if
	you want more flexible joining (for example; setting autojoin to False,
	changing some values before joining, etcetera), you can do this instead:
	- Create the new room with new() first.
	- Get the instance of the new room with self.getByJid().
	- Suit that instance to fit your needs.
	- Use its join() method to finally join the room.

	Returns an integer. 0 for success, 1 for error.
	TODO: have more descriptive return values.
	
	"""
	#get existant instance or create new one
	room = ((id, typ) in rooms and get(id, typ)) or new(id, typ)
	#if the above succeeded, room should now be an instance of the room that was joined
	if type(room) != types.InstanceType:
		return 1
	room.join()
	return 0

def new(id, typ):
	"""Add a room with the specified id and type to the list.
	
	Return its instance. if the Rooms already exists, something unpredictable
	happens (ie: MAKE SURE IT DOESNT HAPPEN).  If you want to have a room
	instance, no matter what, you're advised to do: room = exists(id, typ) and
	get(id, typ) or new(id, typ).
	
	"""
	handler = frontendhandler.getByTyp(typ)

	if exists(id, typ):
		return get(id, typ)
	newroom = handler.MUC(id)
	rooms[(id, typ)] = newroom
	return newroom

def remove(id, typ):
	"""Remove a room with this jid from the list.
	
	Expects the room to exist.  Silently tries to leave the room.
	
	"""
	room = get(id, typ)
	# TODO this part is ugly if it's an xmpp room; upon leaving the server sends
	# a presence stanza (type="unavailable") to show the room has been left, but
	# currently the presence handler freaks when it gets a presence stanza from
	# a room it doesn't know. If that happens, the room is created. So; if the
	# presence stanza is not in before the room is deleted from the list, the
	# room isn't deleted from the database!
	room.leave()
	del rooms[(id, typ)]
