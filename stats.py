# -- coding: utf-8 --
'''
stats.py
///////////////////////////////////////
here we define functions that return statistics about different kinds of stuff, for example: simple, extended, rooms, conversations
///////////////////////////////////////
'''


import time

import config
conf=config.Configuration()
mysql=config.MySQL()
from xmpp_abstract import MUCRooms
roomsHandler=MUCRooms()



def simple():
	"""return basic statistics (uptime, number of factoids, etc)"""

	stats='stats:'

	(uptime,unit)=(time.time()-config.Misc.starttime,"seconds")
	if uptime>3600:
		(uptime,unit)=(uptime/3600,"hours")
	elif uptime>60:
		(uptime,unit)=(uptime/60,"minutes")
	if 1<uptime<2:
		unit=unit[:-1]
	stats+="\nuptime: %d %s"%(uptime,unit)

	results={}
	cursor=mysql.db_r.cursor()


	try:
		cursor.execute("show table status like '%"+"factoids';")
		results['factoids']=cursor.fetchone()
		cursor.execute("show table status like '%"+"reactions_global';")
		results['reactions_global']=cursor.fetchone()
		cursor.execute("show table status like '%"+"reactions_direct';")
		results['reactions_direct']=cursor.fetchone()
		cursor.close()
	except MySQLdb.ProgrammingError, e:
		cursor.close()
		print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n"%e.__str__()
		return "oh dear, the database query failed."
	cursor.close()

	stats+="\nnumber of factoids remembered: %d\nnumber of factoids entered: %d\nnumber of global reactions remembered: %d\nnumber of global reactions entered: %d\nnumber of direct reactions remembered: %d\nnumber of direct reactions entered:%d" % \
	(results['factoids'][4],
	results['factoids'][10],
	results['reactions_global'][4],
	results['reactions_global'][10],
	results['reactions_direct'][4],
	results['reactions_direct'][10])

	return stats


def factoidsAndReactions():
	'''get verbose information about the factoids and reactions'''

	cursor=mysql.db_r.cursor()

	#number of times a factoid or global reaction was replied
	try:
		cursor.execute("select `object`,`count` from `factoids` order by `count` desc limit 5;")
		num_factoids=cursor.fetchall()
		cursor.execute("select `message_in`,`count` from `reactions_global` order by `count` desc limit 5;")
		num_reactions=cursor.fetchall()
		cursor.close()
	except MySQLdb.ProgrammingError, e:
		cursor.close()
		print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n"%e.__str__()
		return "oh dear, the database query failed."

	stats="top requested factoids:"
	for elem in num_factoids:
		stats+="\n    - %s (%d times)"%(elem[0],elem[1])

	stats+="\n\ntop reacted-to's:"
	for elem in num_reactions:
		stats+="\n    - %s (%d times)" %(elem[0],elem[1])

	return stats


def rooms(sorted=False):
	'''return information about the rooms we're in. sort it if sorted==True (bool).'''

	roomlist=roomsHandler.getActive()
	if not roomlist:
		return "I'm not in any rooms atm..."

	if sorted:
		tmp=[]
		for elem in roomlist:
			tmp.append(elem)
		tmp.sort()
		roomlist=tmp
		del tmp

	result="rooms I'm in atm:"
	for elem in roomlist:
		if elem.isActive():
			result+='\n- ' + elem.__str__()
	return result


def extended():
	'''put all other statistics together and blurt them out!'''

	stats=simple()
	stats+='\n\n'+factoidsAndReactions()
	stats+='\n\n'+rooms()

	return stats