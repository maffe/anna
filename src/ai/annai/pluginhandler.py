#!/usr/bin/env python
"""Handle storage of references to plugins.

Works much like the L{aihandler} module in the root. For use inside the
L{ai.annai} module only!

"""
import imp

from ai.annai.plugins import BasePlugin

#: Dictionary mapping pretty names (vals) to real plugin module names (keys).
_name_map = dict(
        dump=u"dump",
        #feedfetcher=u"feedfetcher",
        irrepressible_info=u"irrepressible.info",
        sanna=u"sanna",
        spamblock=u"spamblock",
        test=u"test",
        )
#: Dictionary of references. Keys are pretty versions, values are references.
_refs = {}

class NoSuchPluginError(Exception):
    def __init__(self, name):
        assert(isinstance(name, unicode))
        self._msg = name
    def __unicode__(self):
        return u'No such plugin: "%s"' % self._msg

def about(name):
    """Return the docstring of given plugin as a C{unicode} object."""
    assert(isinstance(name, unicode))
    try:
        return unicode(_refs[name].__doc__)
    except KeyError:
        raise NoSuchPluginError, name

def get_names():
    """Get an iterator with all human-readable names of available plugins."""
    return _refs.iterkeys()

def get_oneonone(plug_name):
    """Get a reference to a OneOnOnePlugin class with given name.

    @raise NoSuchPluginError: Requested plugin does not exist.
    @return: Requested plugin class.
    @rtype: L{BasePlugin}

    """
    try:
        assert(issubclass(_refs[plug_name].OneOnOnePlugin, BasePlugin))
        return _refs[plug_name].OneOnOnePlugin
    except KeyError:
        raise NoSuchPluginError, plug_name

def get_manyonmany(plug_name):
    """Like L{get_oneonone}, but for ManyOnManyPlugin classes."""
    try:
        assert(issubclass(_refs[plug_name].ManyOnManyPlugin, BasePlugin))
        return _refs[plug_name].ManyOnManyPlugin
    except KeyError:
        raise NoSuchPluginError, plug_name

def _update_refs():
    """Update the list of references to plugin modules.

    Note; it is important not to catch any exceptions this function raises
    because it does not release the import lock when failing. Besides, failure
    of this function indicates something is terribly wrong anyway.

    """
    global _refs
    imp.acquire_lock()
    _refs = {}
    for name in [unicode(mod) for mod in _name_map]:
        assert(name not in _refs)
        path = "ai/annai/plugins"
        mod = imp.load_module(name, *imp.find_module(name, [path]))
        _refs[_name_map[name]] = mod
    imp.release_lock()

_update_refs()
