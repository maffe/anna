# -- encoding: utf-8 --

'''use this module as a front-end to the ai module instead of accessing
it directly.'''

import types

#this dictionary will hold which UID is connected to which AID identity
#like this: { 7: 'chat-english' , 23 : 'chat-english' , 57: 'chat-german' }
dictionary = {}

#these functions will be used to access the data stored in the above
#dictionary. note that it is important to use these functions and not access
#the data directly since it is likely that the storage-method will change
#over time.

def getAID( uid ):
	'''get the ai identity (AID) that was assigned to this UID. if no AI was
assigned to this uid, 1 (int) is returned.'''
	try:
		return dictionary[uid]
	except KeyError:
		return 1

def setAID( uid, aid ):
	'''set the AID for this UID. returns an integer. 0 on success, 1 if there
is no such aid.'''
	if not aipool.has_key( aid ):
		return 1
	dictionary[uid] = aid
	return 0



#now we handle the AI modules

def getAIReferenceByAID( aid ):
	'''this function returns a reference to the actual AI module that belongs
	to a given AID. if there is no such AID, 1 (int) is returned.'''
	try:
		return aipool[aid]
	except KeyError:
		return 1

def getAIReferenceByUID( uid ):
	'''this function returns a reference to the actual AI module given a UID.
	if the uid doesn't exist 1 (int) is returned. if the AID assigned to the
	UID is false, 2 (int) is returned.'''

	aid = getAID( uid )
	if type( aid ) == types.IntType:
		return 1

	aireference = getAIReferenceByAID( aid )
	if type( aireference ) == types.IntType:
		return 2
	
	return aireference


#here, we preload all the ai modules in a big pool for quick access later on.
aipool={}
import ai

for elem in ai.__all__:
	#here all ai modules are imported as _ai_<modulename> . then, a reference
	#to all these modules is copied to the aipool dictionary.
	code = 'from ai import %s as _ai_%s ; aipool["%s"] = _ai_%s ' % \
	       ( elem, elem, elem, elem )
	mod = compile( code, __name__, 'exec' )
	eval( mod )
