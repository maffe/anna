"""Fetch ai classes by supplying the name as a string.

When this module is imported it imports all AI modules and keeps a
reference to them. Updating this list of references at runtime is
possible. Fetching references using this module read-only operation and
is threadsafe. Updating the list is not.

The names are case-sensitive.

@TODO: acquire a GIL on update?

"""
import imp

import ai
import communication as c

# Pre-fetch a reference to all classes. Case-sensitive.
_refs = {}

def get_names():
    """Return an iterator with the names of all available AI modules."""
    return _refs.iterkeys()

def get_manyonmany(name):
    """Get the ManyOnMany class of given AI module.

    @param name: The textual representation of the module.
    @type name: C{unicode}
    @raise NoSuchAIError: The specified AI does not exist.

    """
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
    if not isinstance(name, unicode):
        raise TypeError, "name argument must be a unicode object."
    try:
        return _refs[name].OneOnOne
    except KeyError:
        raise NoSuchAIError, name

def _update_refs():
    """Update the list of references with all modules in the AI module."""
    global _refs
    imp.acquire_lock()
    _refs = {}
    # There is no real need for reload() here (yet). Better leave it out.
    #reload(ai)
    for name in [unicode(mod) for mod in ai.__all__]:
        assert(name not in _refs)
        mod = imp.load_module(name, *imp.find_module(name, ["ai"]))
        _refs[name] = mod
        if __debug__:
            if not ("ManyOnMany" in dir(mod) and "OneOnOne" in dir(mod)):
                c.stderr(u"AI module %s does not comply with the API." % name)
                c.stderr(u"\nDEBUG: %r\n", dir(mod))
    imp.release_lock()

class NoSuchAIError(Exception):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return 'No such AI module: "%s".' % self.name

    def __unicode__(self):
        return u'No such AI module: "%s".' % self.name

_update_refs()
