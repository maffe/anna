#!/usr/bin/env python
# -*- coding: utf-8  -*-
#
# original by d0k – http://mooltied.de/drz/
# Licensed under GPLv2 or higher
#
# modified by bb

import sys, re

import stats, aihandler

raw = {
	"^some people are being fangoriously devoured by a gelatinous monster$" : "Hillary’s legs are being digested.",
	"^hello fishbot$" : "Hi %s",
	"^badger badger badger badger badger badger badger badger badger badger badger badger$" : "mushroom mushroom!",
	"^snake$" : "Ah snake a snake! Snake, a snake! Ooooh, it's a snake!",
	"^carrots handbags cheese\.$" : "… toilets russians planets hamsters weddings poets stalin KUALA LUMPUR! pygmies budgies KUALA LUMPUR!",
	"^sledgehammer$" : "sledgehammers go quack!",
	"vinegar(.*)aftershock" : "Ah, a true connoisseur!",
	"^m[oO0]{2,}\?$" : "To moo, or not to moo, that is the question. Whether ’tis nobler in the mind to suffer the slings and arrows of outrageous fish …",
	"^herring$" : "herring(n): Useful device for chopping down tall trees. Also moos (see fish).",
	"hampster" : "%s: There is no 'p' in hamster you retard.",
	"^ag$" : "Ag, ag ag ag ag ag AG AG AG!",
	"^fishbot owns$" : "Aye, I do.",
	"^vinegar$" : "Nope, too sober for vinegar. Try later.",
	"^martian$" : "Don’t run! We are your friends!",
	"^just then, he fell into the sea$" : "Ooops!",
	"^aftershock$" : "mmmm, Aftershock.",
	"^why are you here\?$" : "Same reason. I love candy.",
	"^spoon$" : "There is no spoon.",
	"^bounce$" : "moo",
	"^crack$" : "Doh, there goes another bench!",
	"^you can’t just pick people at random!$" : "I can do anything I like, %s, I’m eccentric! Rrarrrrrgh! Go!",
	"^wertle$" : "moo",
	"^flibble$" : "plob",
	"^www.outwar.com$" : "would you please GO AWAY with that outwar rubbish!",
	"^fishbot created splidge$" : "omg no! Think I could show my face around here if I was responsible for THAT?",
	"^now there’s more than one of them\?$" : "A lot more.",
	"^I want everything$" : "Would that include a bullet from this gun?",
	"^we are getting aggravated.$" : "Yes, we are.",
	"^how old are you, fishbot\?$" : "/me is older than time itself.",
	"^atlantis$" : "Beware the underwater headquarters of the trout and their bass henchmen. From there they plan their attacks on other continents.",
	"^oh god$" : "fishbot will suffice.",
	"^fishbot[\?]*$" : "Yes?",
	"^what is the matrix\?$" : "No-one can be told what the matrix is. You have to see it for yourself.",
	"^what do you need\?$" : "Guns. Lots of guns.",
	"^I know Kungfu$" : "Show me.",
	"^cake$" : "fish",
	"^trout go m[oO0]{2,}$" : "Aye, that’s cos they’re fish.",
	"^Kangaroo$" : "The kangaroo is a four winged stinging insect.",
	"^bass$" : "Beware of the mutant sea bass and their laser cannons!",
	"^trout$" : "Trout are freshwater fish and have underwater weapons.",
	"^where are we\?$" : r"Last time I looked, we were in \2.",
	"^where do you want to go today\?$" : "anywhere but redmond :(.",
	"^fish go m[o0]{2,}$" : "/me notes that %s is truly enlightened.",
	"^(?!trout)(.*?) go m[O0]{2,}$" : "%s: only when they are impersonating fish.",
	"^fish go (?!m[oO0]{2,})(.+)[!]*$" : r"%s lies! fish don’t go \1! fish go m00!",
	"^you know who else (.+)$" : "%s: YA MUM!",
	"^If there’s one thing I know for sure, it’s that fish don’t m00.$" : "%s: HERETIC! UNBELIEVER!",
	"^fishbot: Muahahaha. Ph33r the dark side. :\)$" : "%s: You smell :P.",
	"^ammuu\?$" : "%s: fish go m00 oh yes they do!",
	"^fish$" : "%s: fish go m00!",
	"^/me feeds fishbot hundreds and thousands$" : "MEDI.. er.. FISHBOT",
	"^/me strokes fishbot$" : "/me m00s loudly at %s.",
	"^/me slaps (.*?) around a bit with a large trout$" : "trouted!",
	"^/me has returned from playing counterstrike$" : "like we care fs :(",
	"^/me thinks happy thoughts about (.*?)\.$" : r"/me has plenty of \1. Would you like one, %s?",
	"^/me snaffles (.*?) off fishbot\.$" : ":(",
}

#pre-compile all regex
compiled = []
# compiled: [ (compiled_rex_1, plaintext_answer_1), (compiled_rex_2, plaintext_answer_2) ]

for of, to in raw.items():
	of, to = of.decode( 'utf-8' ), to.decode( 'utf-8' )
	regex = re.compile(of, re.IGNORECASE + re.UNICODE)
	compiled.append( (regex, to) )


def direct( message, identity ):

	if message[:12] == "load module " and message[12:]:
		#prevent trying to load an empty module
		result = aihandler.setAID( identity.getUid(), message[12:] ) #fixme: security?
		identity.send( result and "no such module" or "success!" )

	else:
		identity.send( "Sorry, PMs are not (yet) supported." )


def room( message, sender, room ):

	nick = sender
	conference = str( room )
	text = message

	if nick == room.getNick():
		return
	
	if text == "fishbot, part":
		room.leave()
		return

	elif text == "fishbot, where are you?":
		room.send( stats.rooms() )
		return

	elif text == "fishbot, uptime":
		diff = stats.uptimeSecs()
		msg = 'Uptime: %d seconds. gnarf!' % diff
		room.send( msg )
		return

	if text[:12] == "load module " and text[12:]:
		#prevent trying to load an empty module
		result = aihandler.setAID( room.getUid(), text[12:] ) #fixme: security?
		room.send( result and "no such module" or "success!" )
		return

	#default:
	for regex, to in compiled:

		if regex.match( text ):
			msg = regex.sub( text, to )
			if to.rfind( r'\1' ) != -1:
				var = regex.search(text)
				msg = msg.replace( r'\1', var.group(1) )
			if to.rfind(r'\2') != -1:
				msg = msg.replace( r'\2', conference )
			if to.rfind('%s') != -1:
				sendmsg = msg % nick
			else:
				sendmsg = msg

			room.send( sendmsg )
			return

def invitedToMuc( room, situation, by = None, reason = None ):
	
	if situation != 0:
		room.join()

	msg = '/me m00s contentedly at %s.' % by
	room.send( msg )
