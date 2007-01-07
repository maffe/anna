# -- encoding: utf-8 --

'''
This file manages the plugins loaded by different uids. Note that
the AI module is responsible for actually using these plugins. Also,
since the uid is used as identifier, the plugins are kept even after
changing AI modules.
'''

import plugins

#every callable in this list will be called upon in order. once the
#list has been walked through the result is returned. the plugins
#dictionary maps the lists to the according uids, much like the AIhandler.
_dict = {}

#this dictionary is used to keep a reference to an instance of every
#plugin.
_plugins = {}

def getPlugRef( id ):
	'''Get the reference to the plugin that has this identifier. Raises
	a ValueError if there is no such plugin. This is because the fact
	that a dictionary is used to store the plugins has no real meaning;
	what matters is that this plugin is not found (like a variable that
	does not exist).'''
	try:
		return _plugins[id]
	except KeyError:
		raise ValueError

def addPlugin( uid, pluginID ):
	'''Append given plugin to the end of the list for this uid. If there
	is no entry for this user in the database yet it is created. If there
	is no such plugin, a ValueError is raised.'''
	#raises ValueError
	ref = getPlugRef( pluginID )
	try:
		_dict[uid].append( ref )
	except KeyError:
		_dict[uid] = [ref]

def getAllPlugins():
	'''Return an iterable object holding a textual representation of
	every available plugin in a seperate element.'''
	return plugins.__all__

def getPlugins( uid ):
	'''Get the list of plugins assigned to this uid. Returns an iterable
	object. If there is no plugin assigned to this uid, an empty iterable
	is returned.'''
	try:
		return _dict[uid]
	except KeyError:
		return () # empty tuple

def removePlugin( uid, pluginID ):
	'''Remove this plugin from this uid. Raises a ValueError if this pluginID
	is not assigned to this uid.'''
	try:
		_dict[uid].remove( getPlugRef( pluginID ) )
	except KeyError:
		raise ValueError #prevent raising wrong exception.

def setPluginRefs( uid, referenceList ):
	'''Like getPlugins, except that it sets it.'''
	_dict[uid] = referenceList

for elem in plugins.__all__:
	#here all plugin modules are imported as _plugin_<modulename> . then, a
	#reference to all these modules is copied to the _plugins dictionary.
	code = 'from plugins import %s as _plugin_%s ; _plugins["%s"] = _plugin_%s ' % \
	       ( elem, elem, elem, elem )
	mod = compile( code, __name__, 'exec' )
	eval( mod )
