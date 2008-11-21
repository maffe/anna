'''Annai wrapper for the calculator library.'''

import sys

from ai.annai.plugins import BasePlugin

import simpleparse
# Hack to fool simpleparse into thinking it's a system-wide lib.
sys.modules['simpleparse'] = simpleparse
import calc

parser = calc.MyParser()

class _Plugin(BasePlugin):
    def __unicode__(self):
        return u'calc plugin'

    def process(self, message, reply, sender=None, highlight=True):
        '''Solve a arithmetic problem.

        Only report errors if highlighted.

        '''
        success, children, next = parser.parse(message)
        if success and next == len(message):
            return (message, u'%g' % children[0])
        elif highlight:
            return (u'Failed to parse as arithmetic expression.', reply)

OneOnOnePlugin = _Plugin
ManyOnManyPlugin = _Plugin
