"""This plugin repeats a repeated message (once)."""

from ai.annai.plugins import BasePlugin

class _Plugin(BasePlugin):
	self.sent = False
	self.old = u""

	def __unicode__(self):
		return u"repeat message plugin"

	def process(self, message, reply, *args):
		if message == self.old:
			if not self.sent:
				self.sent = True
				return (message, message)
		else:
			self.old = message
			self.sent = False
		return (message, reply)

OneOnOnePlugin = _Plugin
ManyOnManyPlugin = _Plugin
