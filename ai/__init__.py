# -- coding: utf-8 --
'''
ai/__init__.py
///////////////////////////////////////

the AI module for anna.


      Q & A


Q: WHAT IS THIS MODULE FOR?

A: this module is for taking incoming messages from others and dealing with them. for example, if somebody says "a schnitzel is a gift from the heavens", that entire message should be passed to this module which deals with it in turn. Due to the different languages in the world, it is necessary that this module relies on a different module for each language. Partly because of that, the efficiency of the bot will totally depend on the class of that module. If a module is designed only to return "jawuhl!" at every message, that is what will happen.


Q: WHAT IS THIS MODULE NOT FOR?

A: this module is NOT for dealing with protocol specific events. It should be directly compatible with any front-end; e-mail, a speech2text engine, jabber, etc.


Q: WHAT FUNCTIONALITY IS EXPECTED FROM UNDERLYING AI MODULES?

A: again; not much. the only important thing is that they do not raise unexpected exceptions. this means that they must at least accept calling certain functions and the agreed-on arguments to those functions, even if those functions don't do anything at all.


Q: WHAT CAN THIS MODULE DO?

A: basically, it just takes a string and sends it to another module of choice. this allows for very flexible handling of incoming messages. for example, you could make an 'e-mail' module that sends every incoming message to a number of e-mail addresses, making it act as a mailing list. you could also return a string which will then most probably be handled by the script calling this module. for example: you have a jabber-front end that calls this module. all incoming messages are redirected to a language module of choice, and that module simply returns a bit of text. the jabber front-end messages that piece of text back to whoever triggered the event, and all is done.
(note that the above description is about how this module would work ideally. currently, it is just like a big passive (!) list of all the different modules there are... there's no notable difference, so it's ok ^^ )


Q: WHAT IS THE PRIMARY CAUSE OF DEATH IN THE USA?

A: easy; chuck norris. some sources have told us that this may not be right, though. our investigators are still working on the matter.


Q: IN HOW MANY WAYS CAN YOU HAVE A CONVERSATION?

A: not many. since the bot is currently only a chatbot, this is limited to one-on-one and multi-user. maybe slow communication could also be added (<message type='normal'/>, e-mail), but that's as far as it goes, realisticly. these three different ways can be used pretty flexibly. (also see the next question)


Q: HOW MANY DIFFERENT *TYPES* OF COMMUNICATION EXIST?

A: a whole damned lot! irc, msn, yahoo, icq, jabber, phone, e-mail, snail mail, real-life conversations, you name it! all these types can be realisticly categorized in the three types of conversation mentioned above.


Q: WHAT ARGUMENTS DO THE AI MODULES EXPECT?

### this question still needs a definitive answer, for now it's just a working draft ###

A: this depends on which kind of function you're calling.

def direct(message,name,typ,identity,permissions=[]) - all strings, except 5: list
1) message : intuitively, the content of the message.
2) name    : how to refer to the sender of the message
3) typ     : the type of conversation (jabber, irc, voice, etc)
4) uid     : the unique id of the sender
5) permissions: a list of permissions (e.g.: ['stop', 'protect factoid'] )

def groupchat(message,name,typ,identity,room,permissions=[]) - room = MUC instance
this is roughly the same as the one above, with one notable difference; a universal muc instance is shipped along with the arguments. this allows for doing things in the room without having to know what kind of room it is. for example; .send() will work for every instance, wether it be xmpp, irc or real life.


Q: WHY DOES ONE HAVE TO SPECIFY THE TYPE OF COMMUNICATION?

A: I don't know T_T . I thought it could come in handy.. for example, when storing something in a database, it can be useful to know, additionally to the unique indentifier of the sender for that specific type, what type it is. it just seems more realistic. also, the type can be of influence to the reaction! taking into account the message-limit imposed by msn, you could want to return an excuse instead of too long a message that won't arrive anyway.

///////////////////////////////////////

'''


def chat(lang):
	'''use this function to choose a module that is compatible with instant messaging. most likely these functions will return something with the intention of having it being sent back to the sender.'''
	if lang=='english':
		global ai
		import english as ai
	elif lang=='german':
		global ai
		import german as ai
	else:
		raise ValueError, "there is no module available for '%s'."%lang




pass