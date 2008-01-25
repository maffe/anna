"""AI that focuses on loading a different AI for the user.

The point of this AI is setting it as a default AI for frontends so they
don't have to worry about interaction with peers about this.

"""
from ai import BaseOneOnOne, BaseManyOnMany
import aihandler
import config

CHOOSE_AI = u"Please choose an AI to load from the following list:\n%s"

class _AI(object):
    def __init__(self, party):
        self.party = party
        party.send(self._get_AI_list())

    def _get_AI_class(self, name):
        """Function used to get an AI class from a name."""
        raise NotImplementedError, "Method must be overriden."

    def _get_AI_list(self):
        """Get a textual list of available AIs."""
        def_ai = config.get_conf_copy().misc["default_ai"]
        ais = []
        for name in aihandler.get_names():
            if name.lower() == def_ai.lower():
                name = u" ".join((name, "(default)"))
            ais.append(u"- %s\n" % name)
        return CHOOSE_AI % u"".join(ais).strip()

    def handle(self, message, sender=None):
        """If the message is a valid AI name, load that, otherwise: retry."""
        def_ai = config.get_conf_copy().misc["default_ai"]
        message = message.strip()
        if message == "":
            message = def_ai
        elif message.endswith(" (default)"):
            # If the user thought " (default)" was part of the name, strip.
            message = message[:-len(" (default)")]
        try:
            self.party.set_AI(self._get_AI_class(message)(self.party))
        except aihandler.NoSuchAIError, e:
            self.party.send(u"\n".join((unicode(e), u"Please try again.",
                self._get_AI_list())))
        else:
            self.party.send('"%s" module succesfully loaded.' % message)

class OneOnOne(_AI, BaseOneOnOne):
    def _get_AI_class(self, name):
        return aihandler.get_oneonone(name)
class ManyOnMany(_AI, BaseManyOnMany):
    def _get_AI_class(self, name):
        return aihandler.get_manyonmany(name)
