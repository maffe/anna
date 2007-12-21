"""
internals.py

Module that takes care of everything you need to do with factoids:
add()
delete()
exists()
get()
protect()
unProtect()
isProtected()
"""
#TODO: needs cleaning

import mysql

def add(object, definition, uid):
	"""check if a factoid exists, and if not, add it to the database.

	takes:
	- object and definition (unicode): ... duuh.
	- uid (int): the uid of the thing that is adding this definition

	returns an integer:
	0: success
	1: object already exists
	2: database error: query failed"""


	#check if it doesn't exist already:
	if exists(object):
		return 1

	# do the db thing
	cursor = mysql.db_w.cursor()
	try:
		cursor.execute("insert into `factoids`(`object`,`definition`,`uid`)" \
			+ " values(%s,%s,%s);", (object, definition, uid))
	except cursor.ProgrammingError, e:
		print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n" % e
		return 2
	cursor.close()
	return 0

def delete(object, isadmin = False, silent = False):
	"""delete a factoid.

	takes:
	- object(unicode): object-to-be-deleted
	- isadmin(bool):only if True can protected factoids be deleted

	returns an integer:
	- 0: success
	- 1: object does not exist
	- 2: db error: query failed
	- 3: factoid is protected"""

	#check if it actually exists
	if not exists(object):
		return 1
	#check if it's protected, if so: only continue if jid exists and is an admin
	if not isadmin and isProtected(object):
		return 3


	cursor=mysql.db_w.cursor()
	try:
		cursor.execute("delete from `factoids` where `object` = %s limit 1;" , (object,))
	except cursor.ProgrammingError, e:
		print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n" % e
		return 2
	cursor.close()
	return 0


def exists(object):
	"""return True (bool) if an entry exists for object (unicode) in the
	factoids table, False if not. return 0 (int) if the query failed. it returns
	0 for all errors instead of a specific integer for each seperate error
	because this allows one to do "if exists('bla'):" without getting a false
	"true" when an error occurs."""

	cursor = mysql.db_r.cursor()
	try:
		n = cursor.execute("select `id` from `factoids`" \
			+ "where `object` = %s limit 1;", (object,))
	except cursor.ProgrammingError:
		return 0
	cursor.close()
	if n:
		return True
	else:
		return False

def get(object):
	"""Check the database to see if there's a definition of given object.

	Returns that definition. Also checks if the last character is a question
	mark.

	On failure, return an integer with the error code:
	- 1: object doesn't exist
	- 2: database query error
	
	"""

	#create a cursor from existing database connection
	cursor = mysql.db_r.cursor()
	#execute
	try:
		cursor.execute("select `definition`,`count` from `factoids`" \
			+ "where `object` = %s limit 1;", (object,))
	except cursor.ProgrammingError:
		return 2

	#fetch result.
	result = cursor.fetchone()
	cursor.close()
	# fixme: if load gets high, don't close and reopen the connection
	# but leave it open
	try:
		count = result[1] + 1
	except TypeError: #factoid not defined
		return 1
	else:
		cursor = mysql.db_w.cursor()
		try:
			cursor.execute("update `factoids` set `count`=%s where `object` = %s" \
				+ " and `definition`=%s limit 1;", (count, object, result[0]))
		except cursor.ProgrammingError:
			return 2
		cursor.close()
		# and return! fetchone() returns a tuple with an item for each column; we want the first one.
		return result[0]

def protect( object, protect = True, silent = False):
	"""Set a factoid to be (un)protected.
	
	Usually you'll want only admins to be able to do this.
	example; we want to protect "chuck norris".
	takes:
	- object(unicode): the object of the factoid - in our example: "chuck norris"
	- protect(bool): protect if True, unprotect if False - in our example: True
	returns an integer:
	0: success
	1: unknown object
	2: db error: query failed
	3: it's already protected or unprotected
	
	"""

	#check if factoid exists:
	if not exists(object):
		return 1

	# check if want to protect/unprotect and what the current state is
	isprotected = isProtected(object)
	if protect:
		if isprotected == 1:
			return 3
		else:
			protect = '1'
	else:
		if isprotected == 1:
			protect = '0'
		else:
			return 3

	cursor = mysql.db_w.cursor()
	try:
		cursor.execute("update `factoids` set `protected` = %s where `object` = %s limit 1;",
			(protect, object))
	except cursor.ProgrammingError, e:
		print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n" % e
		return 2
	cursor.close()

	return 0

def unProtect(object):
	"""inverted alias for protect()"""
	return protect(object, protect = False)

def isProtected(object):
	"""check if a factoid is protected (meaning only admins can change it).

	takes:
	- object (unicode): factoid to be checked for protected-ness.

	returns:
	- 0 (int): unprotected
	- 1 (int): protected
	- 2 (int): db error
	- 3 (int): object doesn't exist"""

	cursor = mysql.db_r.cursor()
	try:
		if not cursor.execute("select `protected` from `factoids` where `object` = %s limit 1;",
			(object,)):
			return 3
	except cursor.ProgrammingError, e:
		print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n" % e
		return 2

	result = cursor.fetchone()
	cursor.close()
	return int(result[0])
