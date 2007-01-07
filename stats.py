# -- coding: utf-8 --
'''stats.py
This file defines functions that report statistics about various things like
the rooms the chatbot is active in, the amount of factoids it remembered, etc.'''


import time

import mysql
import rooms as roomsHandler


def simple():
	"""return basic statistics (uptime, number of factoids, etc)"""

	stats = "stats:\n" + uptime()
	results = {}
	cursor = mysql.db_r.cursor()

	try:
		cursor.execute( "show table status like 'factoids';" )
		results['factoids'] = cursor.fetchone()
		cursor.execute( "show table status like 'reactions_global';" )
		results['reactions_global'] = cursor.fetchone()
		cursor.execute( "show table status like 'reactions_direct';" )
		results['reactions_direct'] = cursor.fetchone()
		cursor.close()
	except MySQLdb.ProgrammingError, e:
		cursor.close()
		print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n" % e
		return "oh dear, the database query failed."
	cursor.close()

	stats += '''
number of factoids remembered: %d
number of factoids entered: %d
number of global reactions remembered: %d
number of global reactions entered: %d
number of direct reactions remembered: %d
number of direct reactions entered: %d''' % \
	(results['factoids'][4],
	results['factoids'][10] - 1,
	results['reactions_global'][4],
	results['reactions_global'][10] - 1,
	results['reactions_direct'][4],
	results['reactions_direct'][10] - 1)

	return stats


def factoidsAndReactions():
	'''get verbose information about the factoids and reactions'''

	cursor = mysql.db_r.cursor()

	#number of times a factoid or global reaction was replied
	try:
		cursor.execute( "select `object`,`count` from `factoids` order by `count` desc limit 5;" )
		num_factoids = cursor.fetchall()
		cursor.execute( "select `message_in`,`count` from `reactions_global` order by `count` desc limit 5;" )
		num_reactions = cursor.fetchall()
		cursor.close()
	except MySQLdb.ProgrammingError, e:
		cursor.close()
		print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n" % e
		return "oh dear, the database query failed."

	stats = "top requested factoids:"
	for elem in num_factoids:
		stats += "\n    - %s (%d times)" % ( elem[0], elem[1] )

	stats += "\n\ntop reacted-to's:"
	for elem in num_reactions:
		stats += "\n    - %s (%d times)" % ( elem[0], elem[1] )

	return stats


def rooms( sorted = False ):
	'''return information about the rooms we're in. sort it if sorted == True (bool).'''

	roomlist = roomsHandler.getActive()
	if not roomlist:
		return "I'm not in any rooms atm..."

	#roomsHandler.getActive() returns a tuple, which is unmutable and thus insortable.
	#make it a list first.
	roomlist = list( roomlist )
	#compare the textual representations of the rooms
	roomlist.sort( cmp = lambda x, y: cmp( x.__str__(), y.__str__() ) )

	result = "rooms I'm in atm:"
	for elem in roomlist:
		if elem.isActive():
			result += '\n- %s' % elem

	return result


def uids():
	'''fetch all uid-info'''

	reply = "contacts I know:"

	query_uids = 'select `type`,`name` from `uids`;'
	query_typs = 'select `id`,`type` from `convotypes`;'
	cursor = mysql.db_r.cursor()
	cursor.execute( query_uids )
	uids = list( cursor.fetchall() )
	cursor.execute( query_typs )
	typs = cursor.fetchall()
	cursor.close()

	typs_dict = {} #dictionary with all types. type-id is the key and type-name is the value
	result = {} #all the uids stored together in one tuple for each different type.

	for elem in typs:
		#make the dictionary that holds all the names of the types for easy reference later on
		typs_dict[ elem[0] ] = elem[1]
		#create an empty list for each different type
		result[ elem[0] ] = []

	for elem in uids:
		#put every uid in the result dictionary classed according to its type
		result[ elem[0] ].append( elem[1] )

	for elem in result:
		typ = typs_dict[elem]
		uids = result[elem]
		reply += "\n\n -- %s --" % typ

		for elem in uids:
			reply += "\n%s" % elem

	return reply


def uptime():
	'''Returns the uptime, nicely formatted (in english).'''

	#starttime is usually set by the starting script
	try:
		uptime, unit = time.time() - starttime, "seconds"
	except NameError:
		return "uptime unknown"

	if uptime > 3e5:
		uptime, unit = uptime / 86400, "days"
	elif uptime > 1e4:
		uptime, unit = uptime / 3600, "hours"
	elif uptime > 100:
		uptime, unit = uptime / 60, "minutes"
	if 1 < uptime < 2:
		# not 1 hours but 1 hour
		unit = unit[:-1]

	return "uptime: %d %s" % (uptime, unit)

def uptimeSecs():
	'''Returns the number of seconds the bot is up (will soon be renamed uptime)'''
	try:
		return time.time() - starttime
	except NameError:
		return 0


def extended():
	'''put all other statistics together and blurt them out!'''

	stats = simple()
	stats += '\n\n' + factoidsAndReactions()
	stats += '\n\n' + rooms()
	#stats += '\n\n' + uids()

	return stats
