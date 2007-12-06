"""The AI module for anna.


note: this documentation is relatively old now so it might very well be
possible that the information provided here is not accurate. the idea is
still the same though.


THE PURPOSE OF THIS MODULE

this module is for taking incoming messages from others and dealing with
them. for example, if somebody says "a schnitzel is a gift from the
heavens", that entire message should be passed to this module which
deals with it in turn. Due to the different languages in the world, it
is necessary that this module relies on a different module for each
language. Partly because of that, the efficiency of the bot will totally
depend on the class of that module. If a module is designed only to
return "jawuhl!" at every message, that is what will happen.

TODO: I don't know exactly /what/ I was smoking when I wrote above
      paragraph but it needs some /serious/ revision :P.


WHAT THIS MODULE IS NOT FOR

This module is NOT for dealing with protocol specific events.  It should
be directly compatible with any front-end; e-mail, a speech2text engine,
jabber, etc.


FUNCTIONALITY EXPECTED FROM UNDERLYING AI MODULES

Again; not much. the only important thing is that they do not raise
unexpected exceptions.  This means that they must at least accept
calling certain functions and the agreed-on arguments to those
functions, even if those functions don't do anything at all.


WHAT IS THE PRIMARY CAUSE OF DEATH IN THE USA?

chuck norris.


THE DIFFERENT TYPES OF COMMUNICATION

In our case, there are not many.  Since the bot is currently only a
chatbot, this is limited to one-on-one and multi-user.  Maybe slow
communication could also be added (<message type='normal'/>, e-mail),
but that's as far as it goes, realisticly.  These three different ways
can be used pretty flexibly.  (Also see the next topic.)


THE DIFFERENT *WAYS* OF COMMUNICATING

Now here, there are a whole damned lot! irc, msn, yahoo, icq, jabber,
phone, e-mail, snail mail, real-life conversations, you name it! and
that's just verbal communication.  All these types can be realisticly
categorized in the three types of conversation mentioned above.


THE SUB-MODULES

Ideally, there would be one submodule for every different type of
interaction between persons.  Currently, the list is limited to:
- direct
- room
- invitedToMuc

THE EXPECTED ARGUMENTS TO SUB-MODULES

def direct(message, identity, typ):
    1) message: intuitively, the content of the message.
    2) identity: an instance of a chat-partner.
    3) typ: the type of conversation (jabber, irc, voice, etc)

It is the second argument, identity, that stands at the core of the
seperation between the frontends and the AI.  These conversation-
classes, such as PM() and MUC(), have type-independent methods.  This
allows the AI modules to interact with different chat-partners through
different kinds of conversations without needing to know how.

def room(message, sender, typ, room)

This is roughly the same as the one above.  The sender argument is a
MUCParticipant instance.  The room argument is, obviously, a MUC
instance.

As you can see, even though I have been preaching seperation between AI
and frontends the whole time, the ai methods still want to know what the
type of the conversation is. Actually, "typ" stands for the "way" of
communicating; "xmpp", "irc", etc.  This is necessary for messages that
hold instruction for modifying certain aspects of it. Example: an xmpp
message is received: "join bot@conference.jabber.xs4all.nl".  If we
don't tell the AI module this was an xmpp message, it doesn't know which
network to join a muc on: irc? xmpp?

"""
from _baseclasses import *

__all__=[
    'echo',
#    'annai',
#    'fishbot',
]
