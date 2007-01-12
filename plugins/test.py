#encoding: utf-8
'''Test plugin handler.'''

def process( identity, message, current = None ):
	'''Processes a message. Returns "Test plugin: success." if there was no
	supplied message. If the current computer reply is not None (an empty string
	is not None) " - btw, test plugin successfully loaded" is appended to it.'''

	if current is None:
		return (message, "Test plugin: success.")
	else:
		return (message, "%s - btw, test plugin successfully loaded" % current)
