plughandlers = {}

def register(command,handler):
	try:
		plughandlers[command].append(handler)
	except KeyError:
		plughandlers[command]=[handler]

from plugins import *
