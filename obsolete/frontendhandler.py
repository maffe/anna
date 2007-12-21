"""This module takes care of coordinating the different frontends to the
chatbot.

Use it to, for example, get the reference to a frontend of which you only have
a string with the type.  (Much like aihandler.py, actually).

An example of when you would be using this module: say, somebody says "join
example@example.org".  This should be handled by the currently loaded
ai-module (obviously), but since the ai module is frontend-independent there
is no clean way to import the correct frotnend.  using this module, you can
simply do: frontend = frontendhandler.getByTyp(frontendTyp) and then use that
frontend to join the groupchat.

One more pre is that you don't have to import all frontends for every ai
module seperately.  Instead, they are all imported once (in the frontendpool
dictionary here) and the references are copied.

"""
def existsTyp(typ):
	"""Check if a frontend with name typ exists.
	
	Returns True or False.
	
	"""
	return typ in frontendpool

def getByTyp(typ):
	"""Get the reference to a frontend module by it's name.
	
	This function doesn't catch errors so it's generally not safe to use this
	along with user-input without checking. use existsTyp() for that.

	"""
	return frontendpool[typ]

# Preload all the frontend modules in a big pool for quick access later on.

frontendpool = {}
import frontends

for elem in frontends.__all__:
	# Here all frontend modules are imported as _frontend_<modulename>.  Then, a
	# reference to all these modules is copied to the frontendpool dictionary.
	code = 'from frontends import %s as _frontend_%s ; ' \
	       'frontendpool["%s"] = _frontend_%s' % (elem, elem, elem, elem)
	mod = compile(code, __name__, 'exec')
	eval(mod)
