# -- coding: utf-8 --
'''the nazi game, a very interesting game for nazis and non-nazis alike!'''

import types

from mysql import db_r,db_w



            #### FUNCTIONS FOR THE GAME TABLE ####


def exists(entry):
	'''check if a specified entry exists in the database. return True (bool) if yes, False if no. warning: does NOT catch database query exceptions (to prevent interpreting an error code as True (bool))'''
	cursor=db_r.cursor()
	n=cursor.execute("select `id` from `thenazigame` where `entry` = %s limit 1",entry)
	cursor.close()
	if n:
		return True
	else:
		return False


def add(entry,uid):
	'''add an entry to the database. returns 0 (int) on success, 2 on database error, 1 if the entry already exists.'''
	if exists(entry):
		return 1
	cursor=db_w.cursor()
	try:
		cursor.execute("insert into `thenazigame`(`entry`,`uid`) values(%s,%s)" , (entry,uid) )
	except cursor.ProgrammingError, e:
		print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n"%e.__str__()
		cursor.close()
		return 2
	cursor.close()
	return 0


def getAuthor(entry):
	'''get the uid of who entered the specified entry (str). doesn't catch the query error exception. returns 0 (int) if entry was not found.'''
	cursor=db_r.cursor()
	cursor.execute("select `uid` from `thenazigame` where `entry` = %s limit 1",entry)
	result=cursor.fetchone()
	cursor.close()
	try:
		return result[0]
	except TypeError:
		return 0







          #### FUNCTIONS FOR THE GAMES TABLE ####

def addParticipant(uid,gameid):
	'''add a participant to an existing game . uses getParticipantsRaw() and returns any error code received from that function directly. on database error, return 2 (int). if the uid (int) is already a participant of the game, return 3. #note: these values should be changed if getParticipantsRaw() suddenly uses 2 or 3 as an error code for something different.'''

	raw=getParticipantsRaw(gameid)
	if type(raw)==types.IntType: #on error
		return raw #getParticipantsRaw() uses the same error codes as this function so we can directly pass them through
	raw+=","+uid.__str__()
	cursor=db_w.cursor()
	try:
		n=cursor.execute("update `thenazigames` set `uids` = %s where `id` = %s limit 1" , (raw,gameid) )
		cursor.close()
		return 0
	except cursor.ProgrammingError, e:
		print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n"%e.__str__()
		cursor.close()
		return 2


def getAzi(gameid):
	'''get the characteristic part that goes with the provided gameid(int). returns 1 if the game does not exist, 2 on database error. returns a string containing the result on success.'''
	cursor=db_r.cursor()
	try:
		n=cursor.execute('select `azi` from `thenazigames` where `gameid` = %s limit 1',gameid)
	except cursor.ProgrammingError, e:
		print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n"%e.__str__()
		cursor.close()
		return 2
	result=cursor.fetchone()
	cursor.close()
	if not n:
		return 1
	else:
		return result


def getGameIDs(uid):
	'''get all games a specified uid is participating in. basically, this function checks all games to see if the user is taking place in them, so as you can imagine this is a pretty resource intensive function.'''
	result=[]
	cursor=db_r.cursor()
	try:
		cursor.execute('select `id` from `thenazigames`')
	except cursor.ProgrammingError, e:
		print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n"%e.__str__()
		cursor.close()
		return 2
	for gameid in cursor.__iter__():
		for participant in getParticipants(gameid[0]):
			if participant==uid:
				result.append(gameid)
				break #dont continue checking other participants of this game
	return result


def getParticipants(gameid):
	'''get an iterable object holding all uid's taking part in a thenazigame. takes an integer. if getParticipantsRaw() returns an integer (error) that integer is also returned by this function.'''

	raw=getParticipantsRaw(gameid)
	if type(raw)==types.IntType: #if error
		return raw #pass on the error

	uids=[]
	for elem in raw.split(','):
		uids.append(int(elem))
	cursor.close()
	return uids


def getParticipantsRaw(gameid):
	'''get the participants-list as it is stored in the database without alternation. returns a string on success. this function is mostly used by other functions in this module to prevent duplicating code. returns 1 (int) if the game does not exist and 2 if there was a database error.'''
	cursor=db_r.cursor()
	try:
		n=cursor.execute('select `uids` from `thenazigames` where `gameid` = %s limit 1',gameid)
	except cursor.ProgrammingError, e:
		print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n"%e.__str__()
		cursor.close()
		return 2
	else:
		if not n:
			cursor.close()
			return 1
		result=cursor.fetchone()
		cursor.close()
		return result[0]


def newGame(azi):
	'''create a new thenazigame with charasteristic azi (str). returns a tuple with the id of the game as the only element on success, an integer with an error code otherwise.
notice that by design this can be expected to generate a database error (return value 2 (int)), if this function is started, and then started again while still running. in this case, both times it would try to create a new game with the same gameid, creating a query error for the run that finishes last.'''

	#I don't know how to see what the id was of a newly inserted row so we have to chose between guessing and doing a lot of work. I don't like guessing because it can break stuff, so Ill stick with determining an id upfront and using that.

	cursor=db_w.cursor()
	try:
		cursor.execute("show table status like 'thenazigame'");
	except cursor.ProgrammingError, e:
		print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n"%e.__str__()
		cursor.close()
		return 2
	gameid=cursor.fetchone()[10] #next auto-increment value

	try:
		cursor.execute("insert into `thenazigames`(`id`,`azi`) values(%s,%s)",(gameid,azi))
		cursor.close()
	except cursor.ProgrammingError, e:
		print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n"%e.__str__()
		cursor.close()
		return 2

	return gameid

	#the new game has been created. now we need to lookup what it's id is
