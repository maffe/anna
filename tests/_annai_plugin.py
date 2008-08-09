"""Test an AI module for compliance with the API.

The API is descirbed on U{https://0brg.net/anna/wiki/AI_modules_API}.

This module is intended to be copy/pasted for every AI module that must
be tested. For example, you can use it like this:

>>> from ai.annai.plugins import x as mod
>>> exec open("_annai_plugin.py").read()
>>> # Customize if wanted...
...
>>> unittest.main()

"""
import unittest

#from ai.annai.plugins import x as mod
import frontends

MESSAGES = (
        u"Sample incoming message.",
        u"Message with unix \newlines, mac (\r) and wi\r\ndows.",
        u"Weird \u1234chars and a B\ufeffM.",
        )

def _makeOOOP():
    """Create a OneOnOnePlugin instance suitable for testing.
    
    If the plugin module for this file requires arguments overwrite this
    function as follows, after importing/executing the code in this file:

    >>> del _makeOOO
    >>> def _makeOOO():
    >>>     # Implementation goes here

    """
    global mod
    return mod.OneOnOnePlugin(frontends.BaseIndividual(), [])

def _makeMOMP():
    """Create a ManyOnManyPlugin instance suitable for testing."""
    global mod
    return mod.ManyOnManyPlugin(frontends.BaseGroup(), [])

class TestOneOnOnePlugin(unittest.TestCase):
    def testAPI(self):
        """OneOnOnePlugins must have a set of methods available."""
        ooop = _makeOOOP()
        self.assert_(callable(ooop.__unicode__))
        self.assert_(callable(ooop.process))
        self.assert_(callable(ooop.unloaded))

    def testProcessTypes(self):
        """OneOnOnePlugin processor must accept None and unicode values."""
        ooop = _makeOOOP()
        self.assert_(isinstance(ooop.process(None, None), tuple))
        self.assert_(isinstance(ooop.process(u"", None), tuple))
        self.assert_(isinstance(ooop.process(None, u""), tuple))
        self.assert_(isinstance(ooop.process(u"", u""), tuple))

    def testProcessInput(self):
        """OneOnOnePlugins are not expected to fail with odd input."""
        ooop = _makeOOOP()
        for msg in MESSAGES:
            self.assert_(isinstance(ooop.process(msg, None), tuple))

class TestManyOnManyPlugin(unittest.TestCase):
    def testAPI(self):
        """ManyOnManyPlugins must have a set of methods available."""
        momp = _makeMOMP()
        self.assert_(callable(momp.__unicode__))
        self.assert_(callable(momp.process))
        self.assert_(callable(momp.unloaded))

    def testProcessTypes(self):
        """ManyOnManyPlugin processor must accept None and unicode values."""
        momp = _makeMOMP()
        s = frontends.BaseGroupMember(u"Anonymous")
        self.assert_(isinstance(momp.process(None, None, s, False), tuple))
        self.assert_(isinstance(momp.process(None, None, s, True), tuple))
        self.assert_(isinstance(momp.process(u"", None, s, False), tuple))
        self.assert_(isinstance(momp.process(u"", None, s, True), tuple))
        self.assert_(isinstance(momp.process(None, u"", s, False), tuple))
        self.assert_(isinstance(momp.process(None, u"", s, True), tuple))
        self.assert_(isinstance(momp.process(u"", u"", s, False), tuple))
        self.assert_(isinstance(momp.process(u"", u"", s, True), tuple))
