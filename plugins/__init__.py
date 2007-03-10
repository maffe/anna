"""Information on the plugins can be found on the wiki:
http://0brg.xs4all.nl/anna/wiki/Plugins_API"""

from plugins.factoids import edit as factoids_edit
from plugins.factoids import fetch as factoids_fetch
from plugins.reactions import direct as reactions_direct
from plugins.reactions import global_ as reactions_global
from plugins.reactions import edit as reactions_edit

__all__ = [
	"factoids_edit",
	"factoids_fetch",
#	"gajimtrac",
	"reactions_direct",
	"reactions_global",
	"reactions_edit",
	"spamblock",
	"test",
#	"thenazigame",
]

# The plugins in this list will be loaded automatically for every
# new person (PM). Note that if you enter a non-existant plugin
# here, the bot will crash. Order matters.
default_PM = [
	"factoids_fetch",
	"factoids_edit",
	"reactions_direct",
	"reactions_global",
	"reactions_edit",
	"spamblock",
]

default_MUC = [
	"factoids_fetch",
	"reactions_global",
	"spamblock",
]
