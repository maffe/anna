# -- coding: utf-8 --
'''
Thenazigame, a very interesting game for nazis and non-nazis alike! OK,
seriously now. This is a word-game where two players try to find as much words
that rhyme with a given word as possible. The first time we played this, we
started with "-atie". Which, apparently, rhymes with "nazi" in dutch. When we
discovered that, we decided to call it thenazigame.

This plugin uses two database tables: thenazigames and thenazigame. The first
table holds all different games going on and the uids participating in those
games. The second table holds submissions and the gameid to which those
submissions are posted.
'''

#TODO: this module needs some cleaning up concerning:
# - function-names
# - using exceptions instead of return values

import sys
import types

from mysql import db_r, db_w
import user_identification


def process( identity, message, current = None ):
	'''Process a message to see if it was intented for thenazigame. If it was,
	the plugin will handle it even if there already is a current reaction. This
	means that any output from previous plugins will be lost.
	TODO: decide if this is wanted behaviour.'''

	if not message[:4] == "tng ":
		return current
	message = message[4:].strip()

	try:
		command, message = message.split( ' ', 1 )
	except ValueError:
		return "thenazigame: error"
	
	if command == "add":
		#submit new entry to a game.
		
		#step 1: determine which game id and store it in variable gameid
		try:
			gameid = getGameIDs( identity.getUid() )[0]
		except IndexError:
			#this user is not participating in any games
			pass

		try:
			x, id = message.split( ' ' )[-2:]
			if x == "to":
				#example: "tng add constipatie to 2"
				gameid = int( id )
				message = message.split( ' ' )[:-2]
		except ValueError:
			#note that ValueError is raised by int() and a,b=[]
			pass

		#step 2: add it to the database
		try:
			result = entryAdd( message, gameid, identity.getUid() )
		except NameError:
			#gameid is not defined
			return "Could not determine the game id."
		if result == 0:
			return "k."
		elif result == 1:
			return "That entry already exists."
		elif result == 2:
			return "Whoop, database error."
		else:
			return "An unknown error occured."


	elif command == "create":
		#create a new game
		gameid = newGame( message, identity.getUid() )
		try:
			return "Game %s created with typical bit '%s'" % gameid[0], message
		except TypeError:
			#newGame() returns an int on error; int[0] raises a TypeError
			return "Something appears to have gone wrong."

	elif command == "invite":
		#invite a user to a game. only possible if identity is already
		#a participant of that game.
		
		#step 1: determine which game id and store it in variable gameid
		#code copied from above if-block. maybe this could be a function?
		try:
			gameid = getGameIDs( identity.getUid() )[0]
		except IndexError:
			pass

		try:
			x, id = message.split( ' ' )[-2:]
			if x == "to":
				gameid = int( id )
				message = message.split( ' ' )[:-2]
		except ValueError:
			pass

		#step 2: check if this user is a participant of this game
		try:
			if not participates( identity.getUid(), gameid ):
				return "You need to be a participant of the game before" \
				     + " you can invite someone."
		except NameError:
			return "Didn't understand which game you mean."

		#step 3: get the uid of the invitee
		#TODO: this needs more flexibility
		try:
			uidInvitee = user_identification.getId( message, identity.getType() )
		except ValueError:
			return "User not found."

		#step 4: add the invitee to the game
		result = addParticipant( uidInvitee, gameid )
		if result == 0:
			return "k."
		elif result == 1:
			return "no such game"
		elif result == 2:
			return "Woops, database error."
		elif result == 3:
			return "You are already participating in that game."
		else:
			return "An unknown error occured."
		

            #### FUNCTIONS FOR THE GAME TABLE ####


def entryExists( entry, gameid ):
	'''Check if a specified entry exists in the database (for this game).
	return True (bool) if yes, False if no. Warning: does NOT catch database
	query exceptions (to prevent interpreting an error code as True (bool))
	TODO: this smells fishy - who the hell wrote this? ;P'''
	cursor = db_r.cursor()
	try:
		n = cursor.execute(
			"select `id` from `thenazigame` where `entry` = '%s' and `gameid` = %s limit 1",
			(entry, gameid)
		)
	except cursor.ProgrammingError, e:
		print "\n\n\n%s\n\n\n" % e[1]
		sys.exit()
	cursor.close()
	return n and True or False


def entryAdd( entry, gameid, uid ):
	'''add an entry to the database. returns 0 (int) on success, 2 on database
	error, 1 if the entry already exists.'''
	if entryExists( entry, gameid ):
		return 1
	cursor = db_w.cursor()
	try:
		cursor.execute(
			"insert into `thenazigame`( `entry`, `gameid`, `uid` ) values( %s, %s, %s )",
			(entry, gameid, uid)
		)
	except cursor.ProgrammingError, e:
		print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n" % e
		cursor.close()
		return 2
	cursor.close()
	return 0


def entryGetAuthor( entry, gameid ):
	'''Get the uid of who entered the specified entry (str). Doesn't catch the
	query error exception. Returns 0 (int) if entry was not found.'''
	cursor = db_r.cursor()
	cursor.execute(
		"select `uid` from `thenazigame` where `entry` = %s and `gameid` = %s limit 1",
		(entry, gameid)
	)
	result = cursor.fetchone()
	cursor.close()
	try:
		return result[0]
	except TypeError:
		return 0



          #### FUNCTIONS FOR THE GAMES TABLE ####

def addParticipant( uid, gameid ):
	'''Add a participant to an existing game. Uses _getParticipantsRaw() and
	returns any error code received from that function directly. On database
	error, return 2 (int). If the uid (int) is already a participant of the game,
	return 3.'''

	raw = _getParticipantsRaw( gameid )
	if type( raw ) == types.IntType: #on error
		return raw
		#_getParticipantsRaw() uses the same error codes as this function so we can
		#directly pass them through (dont forget to change here if you change there)
	raw += ",%s" % uid
	cursor = db_w.cursor()
	try:
		n = cursor.execute(
			"update `thenazigames` set `uids` = %s where `id` = %s limit 1",
			(raw, gameid)
		)
		cursor.close()
		return 0
	except cursor.ProgrammingError, e:
		print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n" % e
		cursor.close()
		return 2


def getAzi( gameid ):
	'''Get the characteristic part that goes with the provided gameid(int).
	returns 1 if the game does not exist, 2 on database error. Returns a string
	containing the result on success.'''
	cursor = db_r.cursor()
	try:
		n = cursor.execute(
			'select `azi` from `thenazigames` where `gameid` = %s limit 1',
			gameid
		)
	except cursor.ProgrammingError, e:
		print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n" % e
		cursor.close()
		return 2
	result = cursor.fetchone()
	cursor.close()
	return not n and 1 or result
	#not "return n and result or 1" because result might evaluate to False


def getGameIDs( uid ):
	'''Get all games a specified uid is participating in. Basically, this function
	checks all games to see if the user is taking place in them, so as you can
	imagine this is a pretty resource intensive function.'''
	result = []
	cursor = db_r.cursor()
	try:
		cursor.execute( 'select `id` from `thenazigames`' )
	except cursor.ProgrammingError, e:
		print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n" % e
		cursor.close()
		return 2
	for gameid in iter( cursor ):
		for participant in getParticipants( gameid[0] ):
			if participant == uid:
				result.append( gameid )
				break #dont continue checking other participants of this game
	return result


def getParticipants( gameid ):
	'''Get an iterable object holding all uids taking part in a thenazigame.
	Takes an integer. If _getParticipantsRaw() returns an integer (error) that
	integer is also returned by this function.'''

	raw = _getParticipantsRaw( gameid )
	if type( raw ) == types.IntType: #if error
		return raw #pass on the error

	uids = []
	for elem in raw.split( ',' ):
		uids.append( int( elem ) )
	cursor.close()
	return uids


def _getParticipantsRaw( gameid ):
	'''Get the participants-list as it is stored in the database without
	alternation. Returns a string on success. this function is mostly used by
	other functions in this module to prevent duplicating code. Returns 1 (int) if
	the game does not exist and 2 if there was a database error.'''
	cursor = db_r.cursor()
	try:
		n = cursor.execute(
			'select `uids` from `thenazigames` where `gameid` = %s limit 1',
			gameid
		)
	except cursor.ProgrammingError, e:
		print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n" % e
		cursor.close()
		return 2
	else:
		if not n:
			cursor.close()
			return 1
		result = cursor.fetchone()
		cursor.close()
		return result[0]

def newGame( azi, uid = None ):
	'''Create a new thenazigame with charasteristic azi (str). returns a tuple
	with the id of the game as the only element on success, an integer with an
	error code otherwise. Notice that by design this can be expected to generate a
	database error (return value 2 (int)), if this function is started, and then
	started again while still running. In this case, both times it would try to
	create a new game with the same gameid, creating a query error for the run
	that finishes last.
	If a uid is provided it is automatically added as the first participant of
	the newly created game.'''

	#TODO:
	#I don't know how to see what the id was of a newly inserted row so we have to
	#chose between guessing and doing a lot of work. I don't like guessing because
	#it can break stuff, so Ill stick with determining an id upfront and using
	#that.

	cursor = db_w.cursor()
	try:
		cursor.execute( "show table status like 'thenazigame'" );
	except cursor.ProgrammingError, e:
		print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n" % e
		cursor.close()
		return 2
	gameid = cursor.fetchone()[10] #next auto-increment value

	try:
		cursor.execute(
			"insert into `thenazigames` ( `id`, `azi` ) values( %s, %s )",
			(gameid, azi)
		)
		cursor.close()
	except cursor.ProgrammingError, e:
		print "\n\n  >> DATABASE ERROR: QUERY FAILED <<\n\n  >> %s\n\n" % e
		cursor.close()
		return 2

	if not uid is None:
		addParticipant( uid, gameid )

	return (gameid,)

def participates( uid, gameid ):
	'''Determine if given uid is participating in given game.'''
	return uid in getParticipants( gameid )
