"""crappy docs: all frontend modules should provide MUC and PM classes
that have the following methods:

PM:
__str__():
	return: string - textual representation of this person
	desc:
send( message ):
	return: unspecified
	desc: send a message to the chat-pal
getAI():
	return: AI - instance of the AI module used for this convo
	desc:
getUid():
	return: int - uid
	desc:
setAI( AI ):
	return: unspecified
	desc: set the AI module used for this convo to the given one
isAllowedTo( string sth ):
	return: bool
	desc: checks if this person is allowed to do the specified thing

MUC:
#TODO
"""

__all__ = ["xmpp", "console"]
