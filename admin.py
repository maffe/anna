# -- encoding: utf-8 --
'''Functions only available to admins.'''

import sys
import xmpp

import config


def isAdmin( jid, owneronly = False ):
	'''check if a jid has admin rights.

takes:
- jid (string || xmpp.JID() instance): jid to be checked for admin rights. note: resource will be stripped out.
- owneronly (bool): if True, only return True (bool) if the supplied jid is equal to that of the owner specified in the config file

returns:
- True (bool): if the jid has admin permissions
- False (bool): otherwise'''


	# create an xmpppy JID instance (more flexible)
	jid = xmpp.JID( jid ) # note that if jid already was an xmpp.JID(), this is practically equal to pass
	##check if it's the Pwner himself
	if jid.bareMatch( config.misc['owner_jid'] ):
		return True
	# or one of his bitches, if appropriate
	elif not owneronly and jid.getStripped() in config.admins:
		return True
	else:
		return False



def stop():
	"""kill the bot."""

	#fixme: we need to disconnect etc. how to get the conn variable?
	#conn.send(xmpp.Presence(typ="unavailable"))
	#conn.disconnect()
	print "remote exit initiated"
	sys.exit()
