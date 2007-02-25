import mysql

class Internals:
	"""Functions that handle everything there is to reactions.
	
	Before using this module be sure to set the self.TABLE_NAME string to a suiting
	table name. The name is included directly in the SQL, so watch out for
	injection.
	
	"""
	#TODO: this module needs serious cleaning.
	
	def add(self, message_in, message_out, uid):
		"""Check if a global expression exists, and if not add it to the database.
		
		Takes two strings: listenfor and reaction.
		Returns:
		0: success
		1: reaction is already specified
		2: db error: query failed
		
		"""
		#check existing:
		if self.exists(message_in):
			return 1
	
		# do the db thing
		cursor = mysql.db_w.cursor()
		try:
			cursor.execute(
				"insert into `" + self.TABLE_NAME + "`(`message_in`,`message_out`,`uid`)" \
				+ " values(%s,%s,%s);",
				(message_in, message_out, uid)
			)
		except cursor.ProgrammingError, e:
			print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n" % e
			return 2
		cursor.close()
		return 0
	
	def delete(self, message_in, nocheck = False):
		"""Similar to Factoids.delete():
	
		returns an integer:
		- 0: success
		- 1: object does not exist
		- 2: db error: query failed
		- 3: factoid is protected
		
		"""
		if not self.exists(message_in):
			return 1
		if not nocheck and self.isProtected(message_in):
			return 3
		cursor = mysql.db_w.cursor()
		try:
			cursor.execute(
				"delete from `" + self.TABLE_NAME + "` where `message_in` = %s limit 1;",
				(message_in,)
			)
		except cursor.ProgrammingError, e:
			print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n" % e
			return 2
		cursor.close()
		return 0
	
	def exists(self, message_in):
		"""Determine whether or not a reaction exists."""
	
		cursor = mysql.db_r.cursor()
		try:
			n = cursor.execute(
				"select `id` from `" + self.TABLE_NAME + "` where `message_in` = %s limit 1;",
				(message_in,)
			)
		except cursor.ProgrammingError:
			return 0
		cursor.close()
		return n and True or False
	
	def get(self, message_in):
		"""Check if a string exists in the table and return it. 
	
		Returns the reaction as a string or an integer with errorcode if an error
		ocurred:
		1: message_in unknown
		2: database error: query failed
		
		"""
		cursor = mysql.db_r.cursor()
		try:
			cursor.execute(
				"select `message_out`,`count`,`id` from `" + self.TABLE_NAME \
				+ "` where `message_in` = %s limit 1;",
				(message_in,)
			)
		except cursor.ProgrammingError, e:
			print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n" % e
			return 2
		result = cursor.fetchone()
		cursor.close()
		#TODO if load gets high, don't close and reopen the connection but keep current one
		if result: # increase the used counter
			count = result[1] + 1
			cursor = mysql.db_w.cursor()
			#fixme: catch query failure
			cursor.execute(
				"update `" + self.TABLE_NAME + "` set `count` = %s where `id` = %s limit 1",
				(count, result[2])
			)
			cursor.close()
		try:
			return result[0]
		except TypeError:
			return 1
	
	def protect(self, message_in, protect = True):
		"""Set a reaction to be (un)protected.
		
		Usually you'll want only admins to be able to do this.
	
		Example: we want to protect "hi".
	
		takes:
		- message_in(unicode): the object of the reaction - in our example: "hi"
		- protect(bool): protect if True, unprotect if False - in our example: True
	
		returns an integer:
		0: success
		1: unknown object
		2: db error: query failed
		3: it's already protected or unprotected
		
		"""
		#check if factoid exists:
		if not self.exists(message_in):
			return 1
	
		# check if want to protect/unprotect and what the current state is
		isprotected = self.isProtected(message_in)
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
				"update `" + self.TABLE_NAME + "` set `protected` = %s" 
				+ " where `message_in` = %s limit 1;",
				(protect, message_in)
			)
		except cursor.ProgrammingError, e:
			print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n" % e
			return 2
		cursor.close()
	
		return 0
	
	def unProtect(self, message_in, jid = None):
		"""Inverted alias for protect()."""
		return self.protect(message_in, protect = False)
	
	def isProtected(self, message_in):
		"""Check if a reaction is protected (meaning only admins can change it).
	
		takes:
		- object (unicode): reaction to be checked for protected-ness.
	
		returns:
		- 0 (int): unprotected
		- 1 (int): protected
		- 2 (int): reaction doesn't exist
		- 3 (int): mysql error
		
		"""
		cursor = mysql.db_r.cursor()
		try:
			if cursor.execute(
				"select `protected` from `" + self.TABLE_NAME + "` where `message_in` = %s limit 1;",
				( message_in, )
			) != 1:
				return 2
		except cursor.ProgrammingError, e:
			print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n" % e
			return 3
	
		result = cursor.fetchone()
		cursor.close()
		return int(result[0])
