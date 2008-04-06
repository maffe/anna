class BasePlugin(object):
    """The parent class of all plugins for the annai module."""
    def unloaded(self):
        pass

class PluginError(Exception):
    """Raised by a plugin when it can not continue and should be unloaded.

    Any message passed to this exception on instantiation should be forwarded
    to the identity in question when the exception is caught by the AI module.
    Should only be raised by process() and __init__(). See
    U{https://0brg.net/anna/wiki/Annai_Plugins_API} for more information.

    """
    def __init__(self, msg):
        Exception.__init__(self)
        self._msg = msg
    def __unicode__(self):
        return unicode(self._msg)
