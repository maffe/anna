import logging

import aihandler
import config
from frontends import BaseIndividual

_conf = config.get_conf_copy()
_def_ai_mom = aihandler.get_manyonmany(_conf.misc["default_ai"])
_def_ai_ooo = aihandler.get_oneonone(_conf.misc["default_ai"])
_logger = logging.getLogger("anna." + __name__)

class Individual(BaseIndividual):
    def __init__(self, name):
        self.party = name

    def unicode(self):
        return u"msn://" + self.party

    def get_name(self):
        return self.party

    def get_type(self):
        return u"msn"

    def set_name(self, name):
        assert(isinstance(name, unicode))
        self.party = name

    def send(self, message):
        assert(isinstance(message, unicode))
