"""Fetch ai classes by supplying the name as a string.

When this module is imported it imports all AI modules and keeps a
reference to them. Updating this list of references at runtime is
possible. Fetching references using this module read-only operation and
is threadsafe. Updating the list is not.

The names are case-insensitive so two AI modules that only differ in case are
not allowed.

TODO: acquire a GIL on update?

"""
import imp
import sys

import ai

# Pre-fetch a reference to all classes. Lowercase keynames.
_refs = {}

def get_names():
    """Return an iterator with the names of all available AI modules."""
    return _refs.iterkeys()

def get_manyonmany(name):
    """Get the ManyOnMany class of given AI module."""
    try:
        return _refs[name.lower()].ManyOnMany
    except KeyError:
        raise ValueError, 'No such AI module: "%s".' % name

def get_oneonone(name):
    """Get the OneOnOne class of given AI module."""
    try:
        return _refs[name.lower()].OneOnOne
    except KeyError:
        raise ValueError, 'No such AI module: "%s".' % name

def update_refs():
    """Update the list of references with all modules in the AI module."""
    global _refs
    imp.acquire_lock()
    _refs = {}
    reload(ai)
    for name in ai.__all__:
        assert(name.lower() not in _refs)
        mod = imp.load_module(name, *imp.find_module(name, ["ai"]))
        _refs[name.lower()] = mod
        if __debug__:
            if not ("ManyOnMany" in dir(mod) and "OneOnOne" in dir(mod)):
                print >> sys.stderr, "AI module %s does not comply" % name, \
                            "with the API."
                print >> sys.stderr, "DEBUG:", repr(dir(mod))
    imp.release_lock()

update_refs()
