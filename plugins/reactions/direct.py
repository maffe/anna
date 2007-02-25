"""
Reactions to specified bits of text directed at the chatbot.

A direct reaction is a reaction to something directly addressed to the chatbot.
If the user would just have said "help" in our example, the reaction would not
have been appropriate.

Example:
<user> anna: help
<anna> user: you can define things for me and I will remember them.

See the wiki for more information: http://0brg.xs4all.nl/anna/wiki/

"""
from plugins.reactions import Internals
internals = Internals()
internals.TABLE_NAME = 'reactions_direct'

def process(identity, message, reply):
	"""Check if this message triggers a direct reaction.
	
	If a reply has already been given by a previous plugin (ie.: if not reply is
	None) this plugin exits immediately, without checking anything.
	
	"""
	if not reply is None:
		return (message, reply)
	reply = internals.get(message)
	if isinstance(reply, int):
		reply = None
	return (message, reply)
