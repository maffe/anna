"""Fetch ai classes by supplying the name as a string.

When one of the three important functions defined in this module is
called for the first time all AI modules are imported. Reloading them is
impossible. Getting references using this module is a read-only
operation and is thread-safe.

The names are case-sensitive.

"""
import imp
try:
    import threading as _threading
except ImportError:
    import dummy_threading as _threading

import ai

# Lock for ensuring the _load_refs() method is only run once. Never .release()!
_refs_loaded = _threading.Lock()
# Pre-fetch a reference to all classes. Case-sensitive.
_refs = {}

def _load_refs():
    """Update the list of references with all modules in the AI module.

    This routine can only be run once.

    """
    global _refs, _refs_loaded
    if not _refs_loaded.acquire(False):
        return
    imp.acquire_lock()
    _refs = {}
    for name in [unicode(mod) for mod in ai.__all__]:
        assert(name not in _refs)
        mod = imp.load_module(name, *imp.find_module(name, ["ai"]))
        _refs[name] = mod
    imp.release_lock()

class NoSuchAIError(Exception):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return 'No such AI module: "%s".' % self.name

    def __unicode__(self):
        return u'No such AI module: "%s".' % self.name

def get_names():
    """Return an iterator with the names of all available AI modules."""
    _load_refs()
    return _refs.iterkeys()

def get_manyonmany(name):
    """Get the ManyOnMany class of given AI module.

    @param name: The textual representation of the module.
    @type name: C{unicode}
    @raise NoSuchAIError: The specified AI does not exist.

    """
    _load_refs()
    if not isinstance(name, unicode):
        raise TypeError, "name argument must be a unicode object."
    try:
        return _refs[name].ManyOnMany
    except KeyError:
        raise NoSuchAIError, name

def get_oneonone(name):
    """Get the OneOnOne class of given AI module.

    @param name: The textual representation of the module.
    @type name: C{unicode}
    @raise NoSuchAIError: The specified AI does not exist.

    """
    _load_refs()
    if not isinstance(name, unicode):
        raise TypeError, "name argument must be a unicode object."
    try:
        return _refs[name].OneOnOne
    except KeyError:
        raise NoSuchAIError, name
