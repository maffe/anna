# -- coding: utf-8 --
'''
misc.py
///////////////////////////////////////
Define miscellaneous commands
///////////////////////////////////////
'''

import sys
import xmpp

import config



class Admin:

	def isAdmin(self,jid,owneronly=False):
		'''check if a jid has admin rights.

takes:
- jid (string || xmpp.JID() instance): jid to be checked for admin rights. note: resource will be stripped out.
- owneronly (bool): if True, only return True (bool) if the supplied jid is equal to that of the owner specified in the config file

returns:
- True (bool): if the jid has admin permissions
- False (bool): otherwise'''


		# create an xmpppy JID instance (more flexible)
		jid=xmpp.JID(jid) # note that if jid already was an xmpp.JID(), this is practically equal to pass
		##check if it's the Pwner himself
		if jid.bareMatch(config.misc['owner_jid']):
			return True
		# or one of his bitches, if appropriate
		elif not owneronly and jid.getStripped() in config.admins:
			return True
		else:
			return False



	def stop(self,jid=None,nocheck=False):
		"""kill the bot.
takes:
#conn : xmpp.Client()
jid (str)   : jid calling this function
force (bool): if True jid will be checked for being admin

returns:
- False (bool): unallowed"""

		#fixme: we need to disconnect etc. how to get the conn variable? and! we need to check if this is an admin if nocheck==False
		#conn.send(xmpp.Presence(typ="unavailable"))
		#conn.disconnect()
		print "remote exit initiated"
		sys.exit()


pass