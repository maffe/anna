"""functions that handle everything there is to reactions. Parent class of
ReactionsGlobal and ReactionsDirect. The table names are left out and should be set by the derived classes."""

#TODO: this module needs serious cleaning.

import mysql

def add( message_in, message_out, uid ):
	"""check if a global expression exists, and if not
	add it to the database. takes two strings: listenfor and reaction.
	returns:
	0: success
	1: reaction is already specified
	2: db error: query failed"""




	#check existing:
	if exists( message_in ):
		return 1


	# do the db thing
	cursor = mysql.db_w.cursor()
	try:
		cursor.execute(
			"insert into `" + TABLE_NAME + "`(`message_in`,`message_out`,`uid`)" \
			+ " values(%s,%s,%s);",
			(message_in, message_out, uid)
		)
	except cursor.ProgrammingError, e:
		print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n" % e
		return 2
	cursor.close()
	return 0






def delete( message_in, nocheck = False ):
	"""similar to Factoids.delete():

	returns an integer:
	- 0: success
	- 1: object does not exist
	- 2: db error: query failed
	- 3: factoid is protected"""

	if not exists( message_in ):
		return 1
	if not nocheck and isProtected( message_in ):
		return 3
	cursor=mysql.db_w.cursor()
	try:
		cursor.execute(
			"delete from `" + TABLE_NAME + "` where `message_in` = %s limit 1;",
			(message_in,)
		)
	except cursor.ProgrammingError, e:
		print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n" % e
		return 2
	cursor.close()
	return 0



def exists( message_in ):
	"""just like Factoids.exists()"""

	cursor = mysql.db_r.cursor()
	try:
		n = cursor.execute(
			"select `id` from `" + TABLE_NAME + "` where `message_in` = %s limit 1;",
			(message_in,)
		)
	except cursor.ProgrammingError:
		return 0
	cursor.close()
	if n:
		return True
	else:
		return False




def get( message_in ):
	"""Check if a string exists in the 'global' table and return it. Behaviour
	resembles Factoids.get(). Returns the reaction as a string or an integer
	with errorcode if an error ocurred:
	1: message_in unknown
	2: database error: query failed"""

	cursor = mysql.db_r.cursor()
	try:
		cursor.execute(
			"select `message_out`,`count`,`id` from `" + TABLE_NAME \
			+ "` where `message_in` = %s limit 1;",
			( message_in, )
		)
	except cursor.ProgrammingError, e:
		print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n" % e
		return 2
	result = cursor.fetchone()
	cursor.close()       # fixme: if load gets high, don't close and reopen the connection but keep current one
	if result: # increase the used counter
		count = result[1] + 1
		cursor = mysql.db_w.cursor()
		#fixme: catch query failure
		cursor.execute(
			"update `" + TABLE_NAME + "` set `count` = %s where `id` = %s limit 1",
			(count, result[2])
		)
		cursor.close()
	try:
		return result[0]
	except TypeError:
		return 1




def protect( message_in, protect = True, silent = False ):
	"""set a reaction to be (un)protected. usually you'll want only admins
	to be able to do this.

	example: we want to protect "hi".

	takes:
	- message_in(unicode): the object of the reaction - in our example: "hi"
	- protect(bool): protect if True, unprotect if False - in our example: True

	returns an integer:
	0: success
	1: unknown object
	2: db error: query failed
	3: it's already protected or unprotected"""

	#check if factoid exists:
	if not exists( message_in ):
		return 1

	# check if want to protect/unprotect and what the current state is
	isprotected = isProtected( message_in )
	if protect:
		if isprotected == 1:
			return 3
		else:
			protect = 1
	else:
		if isprotected == 1:
			protect = 0
		else:
			return 3


	cursor = mysql.db_w.cursor()
	try:
		cursor.execute(
			"update `" + TABLE_NAME + "` set `protected` = %s" 
			+ " where `message_in` = %s limit 1;",
			(protect, message_in)
		)
	except cursor.ProgrammingError, e:
		print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n" % e
		return 2
	cursor.close()

	return 0



def unProtect( message_in, jid = None ):
	"""inverted alias for protect()"""
	return protect( message_in, protect = False)





def isProtected( message_in ):
	"""check if a reaction is protected (meaning only admins can change it).

	takes:
	- object (unicode): reaction to be checked for protected-ness.

	returns:
	- 0 (int): unprotected
	- 1 (int): protected
	- 2 (int): reaction doesn't exist
	- 3 (int): mysql error"""

	cursor = mysql.db_r.cursor()
	try:
		if cursor.execute(
			"select `protected` from `" + TABLE_NAME + "` where `message_in` = %s limit 1;",
			( message_in, )
		) != 1:
			return 2
	except cursor.ProgrammingError, e:
		print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n" % e
		return 3

	result = cursor.fetchone()
	cursor.close()
	return int( result[0] )
