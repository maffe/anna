# coding: utf-8

'''Information on the plugins can be found on the wiki:
http://0brg.xs4all.nl/anna/wiki/Plugins_API'''

__all__ = [
	"factoids",
	"gajimtrac",
	"test",
	"thenazigame",
]

# The plugins in this list will be loaded automatically for every
# new person. Note that if you enter a non-existant plugin here,
# the bot will crash. Order matters.
default = [
	"factoids",
]
