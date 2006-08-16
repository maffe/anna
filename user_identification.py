'''functions that allow manipulation of the database of unique user identities. these functions include things like fetching the name corresponding to a certain id or vice-versa, adding new identities, etc.'''



import config
conf=config.Configuration()
mysql=config.MySQL()
from misc import StringFilters
filters=StringFilters()

def addUid(name,typ):
	'''add a new uid to the database. the typ argument is passed directly to the function for checking types, the name is inserted in the database. Do note that if self.getTypeId() raises an exception, it will not be catched. it will just return None if the uid already exists.'''
	try:
		return getId(name,typ)
	except ValueError: #if new, then continue
		try:
			typ=int(typ)
		except ValueError:
			typ=getTypeId(typ)
		query="insert into `uids`(`name`,`type`) values('%s','%d');"%(filters.sql(name),int(typ))
		cursor=mysql.db_w.cursor()
		try:
			cursor.execute(query)
		except mysql.ProgrammingError, e:
			print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n"%e.__str__()
			cursor.close()
			return "database error: query failzored :("
		else:
			cursor.close()
			return getId(name,typ)


def getId(name,typ):
	'''fetch the uid of the user with name name (str) and of type typ (str). return as an integer.'''
	name=filters.sql(name)
	typ=getTypeId(typ)
	query="select `id` from `uids` where `name` = '%s' and `type` = '%d' limit 1;"%(name,typ)
	cursor=mysql.db_r.cursor()
	try:
		n=cursor.execute(query) #.execute() returns the number of rows
	except mysql.ProgrammingError, e:
		print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n"%e.__str__()
		cursor.close()
		return 0 #an integer is expected
	else:
		if not n:
			cursor.close()
			raise ValueError, "user not found"
		result=cursor.fetchone()
		cursor.close()
		return int(result[0])

def getIdNoBullShit(name,typ):
	'''same as getId() but make a new one if it doesn't exist yet'''
	try:
		return getId(name,typ)
	except ValueError:
		addUid(name,typ)
		return getId(name,typ)



def getName(uid):
	'''fetch the row with id = uid (int) from the database and return the name of the user (str)'''
	uid=int(uid) #fixme: not sure, should we check for exception or not?
	query="select `name` from `uids` where `id` = '%d' limit 1;"%uid
	cursor=mysql.db_r.cursor()
	n=cursor.execute(query)
	if not n:
		cursor.close()
		raise ValueError, "user not found"
	result=cursor.fetchone()
	cursor.close()
	return result[0]

def getType(typeid):
	'''returns the conversation type with the specified id (int||str). note that int(id) is executed without for an exception.'''
	typeid=int(typeid)
	query="select `type` from `convotypes` where `id` = '%s' limit 1;"
	cursor=mysql.db_r.cursor()
	n=cursor.execute(query)
	if not n:
		cursor.close()
		raise ValueError, "conversation type not found"
	result=cursor.fetchone()
	cursor.close()
	return result[0]

def getTypeId(typ):
	'''returns the id (int) of the supplied typ(str), fetched from the database that holds the different conversation types. the ValueError exception is raised if it is not an existant conversation type.'''
	try: #maybe it's already an integer...
		return int(typ)
	except ValueError:
		typ=filters.sql(typ)
		query="select `id` from `convotypes` where `type`='%s' limit 1;"%typ
		cursor=mysql.db_r.cursor()
		n=cursor.execute(query)
		if not n:
			cursor.close()
			raise ValueError, "conversation type not found"
		result=cursor.fetchone()
		cursor.close()
		return int(result[0])



def getPermissions(uid):
	'''return an iterable object that holds all the permissions a uid has
#fixme: currently, this just returns 'all' if the uid matches the jid of an admin, hardcoded here. obviously, we need a real system for this.'''
	if int(uid) == 6:
		return ('all',)
	else:
		return ()


def isAllowedTo(uid,whatdoeshewanttodothen):
	'''check if uid (int) is allowed to do whatdoeshewanttodothen (str). returns True (bool) if allowed, False otherwise.'''
	for elem in getPermissions(uid):
		if elem in (whatdoeshewanttodothen,'all'):
			return True
	return False



### hmm... technically speaking, it should be possible (and better) to work without this by simply catching exceptions. if there's a drastic need; it should work.
# def isUid(name,typ):
# 	'''return True (bool) if we already have a uid with this name (str) and type (str||int), False otherwise'''
# 	try:
# 		typ=int(typ)
# 	except ValueError:
# 		typ=getTypeId(typ)
# 	name=filters.sql(name)
# 	query="select `id` from `uids` where `name` = '%s' and `type` = '%d' limit 1;"%(name,typ)
# 	cursor=mysql.db_r.cursor()
# 	n=cursor.execute(query)
# 	cursor.close()
# 	if n:
# 		return True
# 	else:
# 		return False