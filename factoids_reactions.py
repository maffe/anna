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


	def add(self,object,definition,uid):
		"""check if a factoid exists, and if not, add it to the database.

takes:
- object and definition (str): ... duuh.
- uid (int): the uid of the thing that is adding this definition

returns an integer:
0: success
1: object already exists
2: database error: query failed"""


		#check if it doesn't exist already:
		if self.exists(object):
			return 1

		#pass it all through the sqlfilter
		(object,definition,uid)=(filters.sql(object),filters.sql(definition),int(uid))

		# do the db thing
		cursor=MySQL.db_w.cursor()
		try:
			cursor.execute("insert into `factoids`(`object`,`definition`,`uid`) values('%s','%s','%s');"%(object,definition,uid))
		except MySQLdb.ProgrammingError, e:
			print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n"%e.__str__()
			return 2
		cursor.close()
		return 0





	def delete(self,object,isadmin=False,silent=False):
		"""delete a factoid.

takes:
- object(str): object-to-be-deleted
- isadmin(bool):only if True can protected factoids be deleted

returns an integer:
- 0: success
- 1: object does not exist
- 2: db error: query failed
- 3: factoid is protected"""

		#check if it actually exists
		if not self.exists(object):
			return 1
		#check if it's protected, if so: only continue if jid exists and is an admin
		if not isadmin and self.isProtected(object):
			return 3


		cursor=MySQL.db_w.cursor()
		try:
			cursor.execute("delete from `factoids` where `object` = '%s' limit 1;"%filters.sql(object))
		except MySQLdb.ProgrammingError, e:
			print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n"%e.__str__()
			return 2
		cursor.close()
		return 0


	def exists(self,object):
		'''return True (bool) if an entry exists for object (str) in the factoids table, False if not. return 0 (int) if the query failed. it returns 0 for all errors instead of a specific integer for each seperate error because this allows one to do "if exists('bla'):" without getting a false "true" when an error occurs.'''

		object=filters.sql(object)
		cursor=MySQL.db_r.cursor()
		try:
			n=cursor.execute("select `id` from `factoids` where `object`='%s' limit 1;"%object)
		except MySQLdb.ProgrammingError:
			return 0
		cursor.close()
		if n:
			return True
		else:
			return False



	def get(self,object):
		"""check the database to see if there's a definition of object (str)
and return that definition. also checks if the last character is a question
mark.

on failure: returns an integer with the error code:
  1: object doesn't exist
  2: database query error"""

		#prevent mysql injection
		object=filters.sql(object) #replace ' by \'
		#create a cursor from existing database connection
		cursor=MySQL.db_r.cursor()
		#execute
		try:
			cursor.execute("select `definition`,`count` from `factoids` where `object`='%s' limit 1;"%object)
		except MySQLdb.ProgrammingError:
			return 2
		#fetch result.
		result=cursor.fetchone()
		cursor.close()       # fixme: if load gets high, don't close and reopen the connection
	                       # but keep current one
		try:
			count=result[1]+1
		except TypeError: #factoid not defined
			return 1
		else:
			cursor=MySQL.db_w.cursor()
			try:
				cursor.execute("update `factoids` set `count`='%s' where `object`='%s' and `definition`='%s' limit 1;"%(count,object,filters.sql(result[0])))
			except MySQLdb.ProgrammingError:
				return 2
			cursor.close()
			# and return! fetchone() returns a tuple with an item for each column; we want the first one.
			#fixme: I put .__str__() here in case result contains a (long) integer if it was just numbers, but is that possible? if not; just leave this out.
			return result[0].__str__()





	def protect(self,object,protect=True,silent=False):
		''' set a factoid to be (un)protected. usually you'll want only admins to be able to do this.

# example; we want to protect "chuck norris".

takes:
- object(str): the object of the factoid # in our example: "chuck norris"
- protect(bool): protect if True, unprotect if False # in our example: True

returns an integer:
0: success
1: unknown object
2: db error: query failed
3: it's already protected or unprotected'''

		#check if factoid exists:
		if not self.exists(object):
			return 1

		# check if want to protect/unprotect and what the current state is
		isprotected=self.isProtected(object)
		if protect:
			if isprotected==1:
				return 3
			else:
				protect='1'
		else:
			if isprotected==1:
				protect='0'
			else:
				return 3


		object=filters.sql(object)
		cursor=MySQL.db_w.cursor()
		try:
			cursor.execute("update `factoids` set `protected` = %s where `object` = '%s' limit 1;"%(protect,object))
		except MySQLdb.ProgrammingError, e:
			print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n"%e.__str__()
			return 2
		cursor.close()

		return 0



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
- 2 (int): db error
- 3 (int): object doesn't exist'''

		cursor=MySQL.db_r.cursor()
		object=filters.sql(object)
		try:
			if not cursor.execute("select `protected` from `factoids` where `object` = '%s' limit 1;"%object):
				return 3
		except MySQLdb.ProgrammingError, e:
			print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n"%e.__str__()
			return 2

		result=cursor.fetchone()
		cursor.close()
		return int(result[0])



    ### END FACTOIDS ###













    ### REACTIONS ###

class Reactions:
	'''functions that handle everything there is to reactions'''


	def add(self,message_in,message_out,uid):
		"""check if a global expression exists, and if not
add it to the database. takes two strings: listenfor and reaction.
returns:
0: success
1: reaction is already specified
2: db error: query failed"""




		#check existing:
		if self.exists(message_in):
			return 1

		#prepare for sql query
		(message_in,message_out,uid)=(filters.sql(message_in),filters.sql(message_out),int(uid))

		# do the db thing
		cursor=MySQL.db_w.cursor()
		try:
			cursor.execute("insert into `reactions_global`(`message_in`,`message_out`,`uid`) values('%s','%s','%s');"%(message_in,message_out,uid))
		except MySQLdb.ProgrammingError, e:
			print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n"%e.__str__()
			return 2
		cursor.close()
		return 0






	def delete(self,message_in,nocheck=False):
		"""similar to Factoids.delete():

returns an integer:
- 0: success
- 1: object does not exist
- 2: db error: query failed
- 3: factoid is protected"""

		if not self.exists(message_in):
			return 1
		if not nocheck and self.isProtected(message_in):
			return 3
		message_in=filters.sql(message_in)
		cursor=MySQL.db_w.cursor()
		try:
			# FIXME : check protected
			cursor.execute("delete from `reactions_global` where `message_in` = '%s' limit 1;"%message_in)
		except MySQLdb.ProgrammingError, e:
			print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n"%e.__str__()
			return 2
		cursor.close()
		return 0



	def exists(self,message_in):
		'''just like Factoids.exists()'''

		message_in=filters.sql(message_in)
		cursor=MySQL.db_r.cursor()
		try:
			n=cursor.execute("select `id` from `reactions_global` where `message_in`='%s' limit 1;"%message_in)
		except MySQLdb.ProgrammingError:
			return 0
		cursor.close()
		if n:
			return True
		else:
			return False




	def get(self,message_in):
		"""check if a string exists in the 'global' table and return it. behaviour resembles Factoids.get(). returns the reaction as a string or an integer with errorcode if an error ocurred:
1: message_in unknown
2: database error: query failed"""

		message_in=filters.sql(message_in)
		cursor=MySQL.db_r.cursor()
		try:
			cursor.execute("select `message_out`,`count`,`id` from `reactions_global` where `message_in`='%s' limit 1;"%message_in)
		except MySQLdb.ProgrammingError, e:
			print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n"%e.__str__()
			return 2
		result=cursor.fetchone()
		cursor.close()       # fixme: if load gets high, don't close and reopen the connection but keep current one
		if result: # increase the used counter
			count=result[1]+1
			cursor=MySQL.db_w.cursor()
			#fixme: catch query failure
			cursor.execute("update `reactions_global` set `count`=%d where `id`=%d limit 1;"%(int(count),int(result[2])))
			cursor.close()
		try:
			return result[0]
		except TypeError:
			return 1




	def protect(self,message_in,protect=True,silent=False):
		'''set a reaction to be (un)protected. usually you'll want only admins to be able to do this.

# example; we want to protect "hi".

takes:
- message_in(str): the object of the reaction # in our example: "hi"
- protect(bool): protect if True, unprotect if False # in our example: True

returns an integer:
0: success
1: unknown object
2: db error: query failed
3: it's already protected or unprotected'''

		#check if factoid exists:
		if not self.exists(message_in):
			return 1

		# check if want to protect/unprotect and what the current state is
		isprotected=self.isProtected(message_in)
		if protect:
			if isprotected==1:
				return 3
			else:
				protect=1
		else:
			if isprotected==1:
				protect=0
			else:
				return 3


		message_in=filters.sql(message_in)
		cursor=MySQL.db_w.cursor()
		try:
			cursor.execute("update `reactions_global` set `protected` = %d where `message_in` = '%s' limit 1;"%(protect,message_in))
		except MySQLdb.ProgrammingError, e:
			print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n"%e.__str__()
			return 2
		cursor.close()

		return 0



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