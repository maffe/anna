# -- coding: utf-8 --

'''this module takes care of coordinating the different frontends to
the chatbot. use it to, for example, get the reference to a frontend
of which you only have a string with the type. (much like
aihandler.py, actually).

an example of when you would be using this module:
say, somebody says "join example@example.org". this should be handled by
the currently loaded ai-module (obviously), but since the ai module is
frontend-independent there is no clean way to import the correct frotnend.
using this module, you can simply do:
frontend = frontendhandler.getByTyp( frontendTyp )
and then use that frontend to join the groupchat.

one more pre is that you don't have to import all frontends for every ai
module seperately. instead, they are all imported once (in the frontendpool
dictionary here) and the references are copied.'''

def existsTyp( typ ):
	'''check if a frontend with name typ exists. returns True or False.'''
	return typ in frontendpool

def getByTyp( typ ):
	'''get the reference to a frontend module by it's name. this function
doesn't catch errors so it's generally not safe to use this along with
user-input without checking. use existsTyp() for that.'''
	return frontendpool[typ]

#here, we preload all the frontend modules in a big pool for quick
#access later on.

frontendpool = {}
import frontends

for elem in frontends.__all__:
	#here all frontend modules are imported as _frontend_<modulename>.
	#then, a reference to all these modules is copied to the frontendpool
	#dictionary.
	code = 'from frontends import %s as _frontend_%s ; ' \
	       'frontendpool["%s"] = _frontend_%s' % ( elem, elem, elem, elem )
	mod = compile( code, __name__, 'exec' )
	eval( mod )
