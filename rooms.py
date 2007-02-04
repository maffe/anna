# -- coding: utf-8 --
"""use these functions to handle the whole collection of MUC-rooms
known to us, no matter which type.

TODO: make this module really type-independent. - done?"""

import types
import sys

import config
import frontendhandler

#here, a dictionary of all muc-rooms, like this:
#rooms = { (identifier, typ): <module> }
rooms = {}
#this dictionary should only be accessed by getters and setters.


def exists( id, typ ):
	"""return True if have a registered instance of this room."""
	return (id, typ) in rooms


def get( id, typ ):
	"""return the room instance by providing it's identifier and type. raises a
ValueError if not found."""
	try:
		return rooms[ (id, typ) ]
	except KeyError:
		raise ValueError, 'no %s room with id <%s>' % (typ, id)


def getActive():
	"""return an iterable object with all instances of rooms that are active (also look
at getAll() )"""
	result = []
	for elem in rooms.itervalues():
		if elem.isActive():
			result.append( elem )
	return result


def getAll():
	"""return an iterable object with all instances of the known rooms (you will
generally want to use getActive() )"""
	return rooms.itervalues()


def isActive( id, typ ):
	"""similar to exists(), but slightly different: only return True (bool) if the
room is not only known but also active"""
	return (id, typ) in rooms and rooms[ (id, typ) ].isActive()
	#returns False instead of raising KeyError on non-existant room.


def isExistant( id, typ ):
	"""deprecated! use exists()
TODO: delete this function."""
	print >> sys.err, "WARNING: using deprecated frontends.xmpp.rooms.isExistant() function" 
	return (id, typ) in rooms


def join( id, typ ):
	"""join a muc room. use the existing instance if available, create a new one if not.
note: if you want more flexible joining (for example; setting autojoin to False,
changing some values before joining, etcetera), you can do this instead:
- create the new room with new() first
- get the instance of the new room with self.getByJid()
- suit that instance to fit your needs
- use its join() method to finally join the room

returns an integer. 0 for success, 1 for error.
TODO: have more descriptive return values."""
	#get existant instance or create new one
	room = ( (id, typ) in rooms and get(id, typ) ) or new( id, typ )
	#if the above succeeded, room should now be an instance of the room that was joined
	if type( room ) != types.InstanceType:
		return 1
	room.join()
	return 0


def new( id, typ ):
	"""add a room with the specified id and type to the list. return its instance. if the
rooms already exists, something unpredictable happens (ie: MAKE SURE IT DOESNT HAPPEN).
if you want to have a room instance, no matter what, you're advised to do:
room = ( exists(id, typ) and get(id, typ) ) or new( id, typ )"""
	handler = frontendhandler.getByTyp( typ )

	if exists( id, typ ):
		return get( id, typ )
	newroom = handler.MUC( id )
	rooms[ (id, typ) ] = newroom
	return newroom


def remove( id, typ ):
	"""remove a room with this jid from the list. expects the room to exist. silently
tries to leave the room."""
	room = get( id, typ )
	#TODO this part is ugly if it's an xmpp room; upon leaving the server sends a presence
	#stanza (type="unavailable") to show the room has been left, but currently the presence
	#handler freaks when it gets a presence stanza from a room it doesn't know. if that
	#happens, the room is created. so; if the presence stanza is not in before the room
	#is deleted from the list, the room isn't deleted from the database!
	room.leave()
	del rooms[ (id, typ) ]
