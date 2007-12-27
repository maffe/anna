"""Handle storage of references to plugins.

Works much like the L{aihandler} module in the root. For use inside the
L{ai.annai} module only!

"""

# Keeping it simple while that's possible:

plugins = {}
from plugins import test
test.name = u"test"
plugins[u"test"] = test
from plugins import spamblock
spamblock.name = u"test"
plugins[u"spamblock"] = spamblock
