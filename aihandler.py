"""A front-end to the ai modules.

Use this instead of accessing them directly.

"""
from types import *

import ai

#this dictionary will hold which UID is connected to which AID identity
#like this: { 7: 'chat-english' , 23 : 'chat-english' , 57: 'chat-german' }
index = {}

#these functions will be used to access the data stored in the above
#dictionary. note that it is important to use these functions and not access
#the data directly since it is likely that the storage-method will change
#over time.

#here, we preload all the ai modules in a big pool for quick access later on.
_aipool={}

def getAID(uid):
	"""Get the ai identity (AID) that was assigned to this UID.
	
	If no AI was assigned to this uid, 1 (int) is returned.
	
	"""
	try:
		return index[uid]
	except KeyError:
		return 1

def setAID(uid, aid):
	"""Set the AID for this UID.
	
	Returns an integer. 0 on success, 1 if there is no such aid.
	
	"""
	if not _aipool.has_key(aid):
		return 1
	index[uid] = aid
	return 0


#now we handle the AI modules

getAll = _aipool.itervalues
"""Return an iterator holding references to all available ai modules."""

def getAIReferenceByAID(aid):
	"""Return a reference to the actual AI module that belongs to a given AID.
	
	If there is no such AID, 1 (int) is returned.
	
	"""
	try:
		return _aipool[aid]
	except KeyError:
		return 1

def getAIReferenceByUID(uid):
	"""This function returns a reference to the actual AI module given a UID.

	If the uid doesn't exist 1 (int) is returned. If the AID assigned to the
	UID is false, 2 (int) is returned.
	
	"""
	aid = getAID(uid)
	if isinstance(aid, IntType):
		return 1
	aireference = getAIReferenceByAID(aid)
	if isinstance(aireference, IntType):
		return 2
	return aireference


for elem in ai.__all__:
	#here all ai modules are imported as _ai_<modulename> . then, a reference
	#to all these modules is copied to the aipool dictionary.
	code = 'from ai import %s as _ai_%s;_aipool["%s"] = _ai_%s' % \
	       (elem, elem, elem, elem)
	mod = compile(code, __name__, 'exec')
	eval(mod)
	_aipool[elem].ID = elem
