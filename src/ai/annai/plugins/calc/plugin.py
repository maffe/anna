'''Annai wrapper for the calculator library.

Only reacts when the expression can be succesfully parsed. Acts shy (only
reacts when no other plugin reacted yet).

'''
from ai.annai.plugins import BasePlugin

import calc

parser = calc.MyParser()

class _Plugin(BasePlugin):
    def __unicode__(self):
        return u'calc plugin'

    def process(self, message, reply, sender=None, highlight=True):
        '''Solve a arithmetic problem.

        Only report errors if highlighted.

        '''
        try:
            success, result = parser.parse(message)
        except ArithmeticError, e:
            return (message, reply)
        if reply is None and success:
            return (message, u'%g' % result)
        else:
            return (message, reply)

OneOnOnePlugin = _Plugin
ManyOnManyPlugin = _Plugin
