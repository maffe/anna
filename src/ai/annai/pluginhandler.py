#!/usr/bin/env python
"""Handle storage of references to plugins.

Works much like the L{aihandler} module in the root. For use inside the
L{ai.annai} module only! Before this module can be used you MUST call L{start}.

"""
import imp
try:
    import threading as _threading
except ImportError:
    import dummy_threading as _threading

from ai.annai.plugins import BasePlugin
import config

#: Ensure that L{start} is only called once.
_start_lock = _threading.Lock()
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

def start():
    """Perform all actions needed to make the module ready for use.

    Loads and stores the references to plugin modules and populates the
    _name_map dictionary.

    Note; it is important not to catch any exceptions this function raises
    because it does not release the import lock when failing. Besides, failure
    of this function indicates something is terribly wrong anyway.

    """
    global _start_lock, _refs
    if not _start_lock.acquire(False):
        return False
    imp.acquire_lock()
    name_map = config.get_conf_copy().annai_plugins["names"]
    for name in [unicode(mod) for mod in name_map]:
        assert(name not in _refs)
        path = "ai/annai/plugins"
        mod = imp.load_module(name, *imp.find_module(name, [path]))
        _refs[name_map[name]] = mod
    imp.release_lock()
