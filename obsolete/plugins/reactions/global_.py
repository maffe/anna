"""
Reactions to specified messages, not specifically directed to the chatbot.

A global reaction is a reaction to something not directly addressed to the
bot but rather to a remark somebody makes, just like that.

For example:
<user> /me dances *
<anna> /me dances too *

See the wiki for more information: http://0brg.xs4all.nl/anna/wiki/

"""
from plugins.reactions import Internals
internals = Internals()
internals.TABLE_NAME = 'reactions_global'

def process(identity, message, reply):
	"""Check if this message triggers a global reaction.

	If a reply has already been given by a previous plugin (ie.: if not reply is
	None) this plugin exits immediately, without checking anything.
	
	"""
	if reply is not None:
		return (message, reply)
	reply = internals.get(message)
	if isinstance(reply, int):
		reply = None
	return (message, reply)
