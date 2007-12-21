"""Fetch a factoid.

This is a relatively heavy plugin: every message causes
either a database query or a call to yet-another-function (or both).
Reacts to !f0, !f1 and !f2 (to set the status: 0=silent, 1=shy,
2=normal).

Because this plugin is considered so "heavy" it acts SHY: if there is
already a reply constructed by one of the previous plugins (ie:
"if not reply is None:"), it exits immediately.

"""
########################################################################
import types

from plugins.factoids.internals import get #it's FETCH.py ;)
import stringfilters as filters

_status = {}
"""The key is the uid and the value is the status for this uid.

0: silent
1: only talk if an answer is found
2: say "IDK D00D" if no answer is found

"""
_defaultStatus = 2

def process(identity, message, reply):
	"""Take the original message and determine what to do with it based on the
	status of this plugin.
	
	"""
	if not reply is None:
		return (message, reply)
	uid = identity.getUid()
	result = None
	try:
		status = _status[uid]
	except KeyError:
		status = _defaultStatus

	#Eventhough this block of code belongs in _checkStatus(), it is better here
	#because the status is already known.
	if message == "!f":
		return (message, str(status))

	#Check if this message was meant to modify the status.
	elif message.startswith("!f"):
		return (message, _checkStatus(message, uid))

	elif status == 0:
		return (message, reply)

	elif message[:8].lower() == "what is ":
		result = get(filters.stripQM(message[8:]))
	elif message[:7].lower() == "what's ":
		result = get(filters.stripQM(message[7:]))
	#TODO: why don't we call filters.stripQM() on the line below?
	elif message[:17].lower() == "do you know what " and message.strip("?").endswith(" is"):
		result = get(message.strip("?")[17:-3])
	if isinstance(result, types.IntType):
		if status != 2:
			#We don't have the result, but we're not going to say it:
			result = None
		elif result == 1:
			result = "Idk.. can you tell me?"
		elif result == 2:
			result = "whoops... db error :s"
		else: #unspecified error
			result = "an error ocurred"

	if not result and status and message.endswith("?"):
		#Finds factoids like "cpu?".
		result = get(message.strip("?"))
		if isinstance(result, types.IntType):
			result = None
			#Never complain about a not-found factoid, even if status is 2.

	return result is None and (message, reply) or (message, result)

def _checkStatus(message, uid):
	"""Check if the message was sent to adjust the status of the plugin."""
	if message == "!f0":
		_status[uid] = 0
	elif message == "!f1":
		_status[uid] = 1
		return "I will only respond to questions if I know the answer."
	elif message == "!f2":
		_status[uid] = 2
		return "I will tell you about things I do not know."
	else:
		return "Unrecognized command"
