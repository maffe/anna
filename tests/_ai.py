"""Test an AI module for compliance with the API.

The API is descirbed on U{https://0brg.net/anna/wiki/AI_modules_API.

This module is intended to be copy/pasted for every AI module that must
be tested. For example, you can use it like this:

>>> from ai import x as mod
>>> exec open("_ai.py").read()
>>> # Customize if wanted...
...
>>> unittest.main()

"""
import unittest

#import ai.x as mod
import frontends

def _makeOOO():
    """Create a OneOnOne instance suitable for testing."""
    global mod
    return mod.OneOnOne(frontends.BaseIndividual())

class OneOnOneAPI(unittest.TestCase):
    
    def testInit(self):
        """OneOnOne initializer must accept only one arg: Individual."""
        _makeOOO()

    def testHandle(self):
        """OneOnOne must have a handler for incoming messages."""
        ooo = _makeOOO()
        self.assert_(hasattr(ooo, "handle"))

class OneOnOneHandle(unittest.TestCase):
    messages = (
            u"Sample incoming message.",
            u"Message with unix \newlines, mac (\r) and wi\r\ndows.",
            u"Weird \u1234chars and a B\ufeffM.",
            )

    def testEmpty(self):
        """OneOnOne instances must accept empty messages."""
        ooo = _makeOOO()
        for msg in self.messages:
            ooo.handle(msg)

    def testMessageType(self):
        """OneOnOne instances must accept unicode messages."""
        ooo = _makeOOO()
        ooo.handle(u"x")

if __name__ == "__main__":
    unittest.main()
