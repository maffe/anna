# -- coding: utf-8 --
'''
factoids_reactions.py
///////////////////////////////////////
Check for factoids or reactions and answer to it
///////////////////////////////////////
'''

import MySQLdb
import xmpp

from config import MySQL
from config import Configuration
conf=Configuration()
from misc import StringFilters
filters=StringFilters()
from misc import Admin
admins=Admin()

    ### FACTOIDS ###

class Factoids:
	'''functions that delete, add, fetch, protect, etc factoids'''

	def get(self,text,silent=False):
		"""check the database to see if there's a definition of 'text'
and return that definition if it exists, or an excuse if
it doesn't. also checks if the last character is a question
mark.

takes:
- the object to look up (str)
- on failure: return excuse if silent=False, return False if True (bool)"""

		#define object and prevent mysql injection
		object=text.strip("?")
		object=filters.sql(object) #replace ' by \'
		#create a cursor from existing database connection
		cursor=MySQL.db_r.cursor()
		#execute
		try:
			cursor.execute("select `definition`,`count` from `factoids` where `object`='%s' limit 1;"%object)
		except MySQLdb.ProgrammingError:
			return "ah scheit, database error"
		#fetch result.
		result=cursor.fetchone()
		cursor.close()       # fixme: if load gets high, don't close and reopen the connection
	                       # but keep current one
		try:
			count=result[1]+1
		except TypeError:
			if silent:
				return False
			else:
				return "I don't know... can you tell me?"
		else:
			if not silent:
				cursor=MySQL.db_w.cursor()
				try:
					cursor.execute("update `factoids` set `count`='%s' where `object`='%s' and `definition`='%s' limit 1;"%(count,object,filters.sql(result[0])))
				except MySQLdb.ProgrammingError:
					return "ah scheit, database error"
				cursor.close()
			# and return! fetchone() returns a tuple with an item for each column; we want the first one
			return result[0]


	def add(self,object,definition,uid,isadmin=False):
		"""check if a factoid exists, and if not, add it to the database. """


##### FIXME: MOVE THIS TO THE AI MODULE ######

		# if definition is 'protected' and jid is an admin, it means he wanted to protect the value
		# if the jid is not an admin, just enter the factoid with definition "protected"
# 		if admins.isAdmin(jid):
# 			if definition=='protected':
# 				return self.protect(object,nocheck=True) #we already know it's an admin; nocheck.
# 			elif definition=="public":
# 				return self.unProtect(object,nocheck=True)

		#check existing:
		exists=self.get(object,silent=True)
		if exists:
			if exists.lower() == definition.lower(): # it's a known definition
				return "I know"
			else: # We have another definition
				return "but... but... %s is %s"%(object,exists)

		#pass it all through the sqlfilter
		(object,definition,uid)=(filters.sql(object),filters.sql(definition),int(uid))

		# do the db thing
		cursor=MySQL.db_w.cursor()
		try:
			cursor.execute("insert into `factoids`(`object`,`definition`,`uid`) values('%s','%s','%s');"%(object,definition,uid))
		except MySQLdb.ProgrammingError, e:
			print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n"%e.__str__()
			return "mucho shitheads dancing in line; the database query fails!"
		cursor.close()
		return "k."





	def delete(self,object,isadmin=False,silent=False):
		"""delete a factoid.

takes:
- object(str): object-to-be-deleted
- isadmin(bool):only if True can protected factoids be deleted
- silent(bool): return False instead of error messages on failure if silent==True"""

		#check if it actually exists
		if not self.get(object,silent=True):
			if silent:
				return False
			else:
				return "I don't even know what that is"
		#check if it's protected, if so: only continue if jid exists and is an admin
		if not isadmin and self.isProtected(object):
			return "that factoid is protected; only an admin can delete it."


		cursor=MySQL.db_w.cursor()
		try:
			cursor.execute("delete from `factoids` where `object` = '%s' limit 1;"%filters.sql(object))
		except MySQLdb.ProgrammingError, e:
			print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n"%e.__str__()
			return "kartoffelschnitzel, the database query failed!"
		cursor.close()
		return "k."




	def protect(self,object,protect=True,silent=False):
		''' set a factoid to be (un)protected. usually you'll want only admins to be able to do this.

# example; we want to protect "chuck norris".

takes:
- object(str): the object of the factoid # in our example: "chuck norris"
- protect(bool): protect if True, unprotect if False # in our example: True
- silent(bool): if True, return False(bool) instead of error_message (str) on failure

returns:
- True (bool): success
- False(bool) || error_message (str): failure (see above)'''

		#check if factoid exists:
		if not self.get(object,silent=True):
			if silent:
				return False
			else:
				return "I don't know what '%s' is"%object

		# check if want to protect/unprotect and what the current state is
		isprotected=self.isProtected(object)
		if protect:
			if isprotected==1:
				if silent:
					return False
				else:
					return "'%s' is already protected"%object
			else:
				protect='1'
		else:
			if isprotected==1:
				protect='0'
			else:
				if silent:
					return False
				else:
					return "'%s' wasn't protected in the first place"%object


		object=filters.sql(object)
		cursor=MySQL.db_w.cursor()
		try:
			cursor.execute("update `factoids` set `protected` = %s where `object` = '%s' limit 1;"%(protect,object))
		except MySQLdb.ProgrammingError, e:
			print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n"%e.__str__()
			if silent:
				return False
			else:
				return "scheit! database error."
		cursor.close()

		return silent or "k."



	def unProtect(self,object):
		'''inverted alias for self.protect()'''
		return self.protect(object,protect=False)





	def isProtected(self,object):
		'''check if a factoid is protected (meaning only admins can change it).

takes:
- object (str): factoid to be checked for protected-ness.

returns:
- 0 (int): unprotected
- 1 (int): protected
- 2 (int): object doesn't exist
- 3 (int): mysql error'''

		cursor=MySQL.db_r.cursor()
		object=filters.sql(object)
		try:
			if cursor.execute("select `protected` from `factoids` where `object` = '%s' limit 1;"%object) != 1:
				return 2
		except MySQLdb.ProgrammingError, e:
			print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n"%e.__str__()
			return 3

		result=cursor.fetchone()
		cursor.close()
		return int(result[0])



    ### END FACTOIDS ###













    ### REACTIONS ###

class Reactions:
	'''functions that handle everything there is to reactions'''


	def get(self,message_in,silent=True,user=None):
		"""check if a string exists
				in the 'global' table
				and return it (or False)

				behaviour resembles factoid_get()

				user (str) is used to replace %(user)s with."""

		message_in=filters.sql(message_in)
		cursor=MySQL.db_r.cursor()
		try:
			cursor.execute("select `message_out`,`count`,`id` from `reactions_global` where `message_in`='%s' limit 1;"%message_in)
		except MySQLdb.ProgrammingError, e:
			print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n"%e.__str__()
			return "that fucking database query failed!"
		result=cursor.fetchone()
		cursor.close()       # fixme: if load gets high, don't close and reopen the connection
												 # but keep current one
		if result: # increase the used counter
			count=result[1]+1
			cursor=MySQL.db_w.cursor()
			#fixme: catch query failure
			cursor.execute("update `reactions_global` set `count`=%d where `id`=%d limit 1;"%(int(count),int(result[2])))
			cursor.close()
		try:
			result=result[0]
			if user:
				dictionary={'user':user}
			try:
				return result%dictionary
			except KeyError, e: # prevent exit on invalid key (looks complicated... I couldn't make it look better)
				return "somebody said I should say '%s' now, but I don't know what to replace '"%result + "%(" + "%s)s"%e[0] + "' with "
			except ValueError: # handle incorrect stanza (eg.: %(user) instead of %(user)s )
				return "somebody told me I should say '%s' now, but I think something is wrong there..."%result
			except NameError:
				return result
			#fixme: check all possible exceptions that can occur
			#return result
		except TypeError:
			if silent:
				return False
			else:
				return "sorry, never heard of it."




	def add(self,message_in,message_out,uid):
		"""check if a global expression exists, and if not
add it to the database. takes two strings: listenfor and reaction"""




		#check existing:
		exists=self.get(message_in,silent=True)
		if exists:
			return "but... but... the reaction to %s is %s "%(message_in,exists)

		#prepare for sql query
		(message_in,message_out,uid)=(filters.sql(message_in),filters.sql(message_out),int(uid))

		# do the db thing
		cursor=MySQL.db_w.cursor()
		try:
			cursor.execute("insert into `reactions_global`(`message_in`,`message_out`,`uid`) values('%s','%s','%s');"%(message_in,message_out,uid))
		except MySQLdb.ProgrammingError, e:
			print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n"%e.__str__()
			return "oh dear, the database query failed."
		cursor.close()
		return "k."




	def delete(self,message_in,silent=False,nocheck=False):
		"""check if a global reaction exists and delete it if it does."""

		if not self.get(message_in,silent=True):
			if silent:
				return False
			else:
				return "I don't even know what to say to that..."
		if not nocheck and self.isProtected(message_in):
			if silent:
				return False
			else:
				return "that reaction is protected; only an admin can change it. sorry.."
		message_in=filters.sql(message_in)
		cursor=MySQL.db_w.cursor()
		try:
			# FIXME : check protected
			cursor.execute("delete from `reactions_global` where `message_in` = '%s' limit 1;"%message_in)
		except MySQLdb.ProgrammingError, e:
			print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n"%e.__str__()
			return "crap on a fuckstick, the query failed!"
		cursor.close()
		return "k."




	def protect(self,message_in,protect=True,silent=False):
		''' set a reaction to be (un)protected. usually you'll want only admins to be able to do this.

# example; we want to protect "hi".

takes:
- message_in(str): the object of the reaction # in our example: "hi"
- protect(bool): protect if True, unprotect if False # in our example: True
- silent(bool): if True, return False(bool) instead of error_message (str) on failure

returns:
- True (bool) || "k.": success
- False(bool) || error_message (str): failure (see above)'''

		#check if factoid exists:
		if not self.get(message_in,silent=True):
			if silent:
				return False
			else:
				return "I don't even know what to say to that..."

		# check if want to protect/unprotect and what the current state is
		isprotected=self.isProtected(message_in)
		if protect:
			if isprotected==1:
				if silent:
					return False
				else:
					return "The reaction to '%s' is already protected"%message_in
			else:
				protect='1'
		else:
			if isprotected==1:
				protect='0'
			else:
				if silent:
					return False
				else:
					return "The reaction to '%s' wasn't protected in the first place"%message_in


		message_in=filters.sql(message_in)
		cursor=MySQL.db_w.cursor()
		try:
			cursor.execute("update `reactions_global` set `protected` = %d where `message_in` = '%s' limit 1;"%(protect,message_in))
		except MySQLdb.ProgrammingError, e:
			print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n"%e.__str__()
			if silent:
				return False
			else:
				return "scheit! database error."
		cursor.close()

		return silent or "k."



	def unProtect(self,message_in,jid=None):
		'''inverted alias for self.protect()'''
		return self.protect(message_in,protect=False)





	def isProtected(self,message_in):
		'''check if a reaction is protected (meaning only admins can change it).

takes:
- object (str): reaction to be checked for protected-ness.

returns:
- 0 (int): unprotected
- 1 (int): protected
- 2 (int): reaction doesn't exist
- 3 (int): mysql error'''

		cursor=MySQL.db_r.cursor()
		message_in=filters.sql(message_in)
		try:
			if cursor.execute("select `protected` from `reactions_global` where `message_in` = '%s' limit 1;"%message_in) != 1:
				return 2
		except MySQLdb.ProgrammingError, e:
			print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n"%e.__str__()
			return 3

		result=cursor.fetchone()
		cursor.close()
		return int(result[0])




     ### END REACTIONS ###

pass