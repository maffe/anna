"""This plugin lets anna become Captain Planet!"""

from ai.annai.plugins import BasePlugin
import re

class _Plugin(BasePlugin):
    _HOOKS = frozenset([u'earth', u'fire', u'wind', u'water', u'heart'])
    _STRIPREX = re.compile(u'^(.*?)[.!]*$', re.DOTALL)

    def __init__(self, identity, args):
        self._hits = set()

    def __unicode__(self):
        return u'Captain Planet plugin'

    def process(self, message, reply, *args):
        stripped = self._STRIPREX.match(message).group(1).lower()
        if stripped in self._HOOKS:
            self._hits.add(stripped)
            if self._hits == self._HOOKS:
                self._hits.clear()
                return (message, u'By your powers combined, I am Captain Planet!')
        return (message, reply)

OneOnOnePlugin = _Plugin
ManyOnManyPlugin = _Plugin
