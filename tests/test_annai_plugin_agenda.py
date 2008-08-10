#!/usr/bin/env python
from ai.annai.plugins import agenda as mod
exec open("_annai_plugin.py").read()
del _makeOOOP, _makeMOMP
def _makeOOOP():
    global mod
    return mod.OneOnOnePlugin(frontends.BaseIndividual(), [u"x"])
def _makeMOMP():
    global mod
    return mod.ManyOnManyPlugin(frontends.BaseGroup(), [u"x"])

if __name__ == "__main__":
    unittest.main()
