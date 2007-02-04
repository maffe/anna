# vim:fileencoding=utf-8
################################################################################

"""Information on the plugins can be found on the wiki:
http://0brg.xs4all.nl/anna/wiki/Plugins_API"""

#from factoids import factoids as factoids_edit
from factoids import fetch as factoids_fetch

__all__ = [
#	"factoids_edit",
	"factoids_fetch",
#	"gajimtrac",
#	"reactions",
	"test",
#	"thenazigame",
]

# The plugins in this list will be loaded automatically for every
# new person (PM). Note that if you enter a non-existant plugin
# here, the bot will crash. Order matters.
default_PM = [
#	"factoids_edit",
#	"factoids_fetch",
#	"reactions",
]

default_MUC = [
#	"factoids_fetch",
]
