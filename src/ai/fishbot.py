# Python version by U{d0k <http://doktorz.mooltied.de/>} based on
# commands listed on U{http://www.telkman.co.uk/f/commands.php}.
# Modified by bb.
#
# Licensed under the MIT license, see /COPYRIGHT.txt for more
# details.

import re
import sys

import ai
import aihandler
import frontends

raw = {
    u"^some people are being fangoriously devoured by a gelatinous monster$": u"Hillary\u2019s legs are being digested.",
    u"^hello fishbot$": u"Hi %s",
    u"^badger badger badger badger badger badger badger badger badger badger badger badger$" : "mushroom mushroom!",
    u"^snake$": u"Ah snake a snake! Snake, a snake! Ooooh, it\u2019s a snake!",
    u"^carrots handbags cheese\.$": u"\u2026 toilets russians planets hamsters weddings poets stalin KUALA LUMPUR! pygmies budgies KUALA LUMPUR!",
    u"^sledgehammer$": u"sledgehammers go quack!",
    u"vinegar(.*)aftershock": u"Ah, a true connoisseur!",
    u"^m[oO0]{2,}\?$": u"To moo, or not to moo, that is the question. Whether \u2019tis nobler in the mind to suffer the slings and arrows of outrageous fish \u2026",
    u"^herring$": u"herring(n): Useful device for chopping down tall trees. Also moos (see fish).",
    u"hampster": u"%s: There is no 'p' in hamster you retard.",
    u"^ag$": u"Ag, ag ag ag ag ag AG AG AG!",
    u"^fishbot owns$": u"Aye, I do.",
    u"^vinegar$": u"Nope, too sober for vinegar. Try later.",
    u"^martian$": u"Don\u2019t run! We are your friends!",
    u"^just then, he fell into the sea$" : u"Ooops!",
    u"^aftershock$": u"mmmm, Aftershock.",
    u"^why are you here\?$": u"Same reason. I love candy.",
    u"^spoon$": u"There is no spoon.",
    u"^bounce$": u"moo",
    u"^crack$": u"Doh, there goes another bench!",
    u"^you can\u2019t just pick people at random!$" : "I can do anything I like, %s, I\u2019m eccentric! Rrarrrrrgh! Go!",
    u"^wertle$": u"moo",
    u"^flibble$": u"plob",
    u"^www.outwar.com$": u"would you please GO AWAY with that outwar rubbish!",
    u"^fishbot created splidge$": u"omg no! Think I could show my face around here if I was responsible for THAT?",
    u"^now there\u2019s more than one of them\?$": u"A lot more.",
    u"^I want everything$": u"Would that include a bullet from this gun?",
    u"^we are getting aggravated.$": u"Yes, we are.",
    u"^how old are you, fishbot\?$": u"/me is older than time itself.",
    u"^atlantis$": u"Beware the underwater headquarters of the trout and their bass henchmen. From there they plan their attacks on other continents.",
    u"^oh god$": u"fishbot will suffice.",
    u"^fishbot[\?]*$": u"Yes?",
    u"^what is the matrix\?$": u"No-one can be told what the matrix is. You have to see it for yourself.",
    u"^what do you need\?$": u"Guns. Lots of guns.",
    u"^I know Kung ?fu\.?$": u"Show me.",
    u"^cake$": u"fish",
    u"^trout go m[oO0]{2,}$": u"Aye, that\u2019s cos they\u2019re fish.",
    u"^Kangaroo$": u"The kangaroo is a four winged stinging insect.",
    u"^bass$": u"Beware of the mutant sea bass and their laser cannons!",
    u"^trout$": u"Trout are freshwater fish and have underwater weapons.",
    u"^where are we\?$": ur"Last time I looked, we were in \2.",
    u"^where do you want to go today\?$": u"anywhere but redmond :(.",
    u"^fish go m[o0]{2,}$": u"/me notes that %s is truly enlightened.",
    u"^(?!trout)(.*?) go m[O0]{2,}$": u"%s: only when they are impersonating fish.",
    u"^fish go (?!m[oO0]{2,})(.+)[!]*$": u"%s lies! fish don\u2019t go \\1! fish go m00!",
    u"^you know who else (.+)$": u"%s: YA MUM!",
    u"^If there\u2019s one thing I know for sure, it\u2019s that fish don\u2019t m00.$": u"%s: HERETIC! UNBELIEVER!",
    u"^fishbot: Muahahaha. Ph33r the dark side. :\)$": u"%s: You smell :P.",
    u"^ammuu\?$": u"%s: fish go m00 oh yes they do!",
    u"^fish$": u"%s: fish go m00!",
    u"^/me feeds fishbot hundreds and thousands$": u"MEDI.. er.. FISHBOT",
    u"^/me strokes fishbot$": u"/me m00s loudly at %s.",
    u"^/me slaps (.*?) around a bit with a large trout$": u"trouted!",
    u"^/me has returned from playing counterstrike$": u"like we care fs :(",
    u"^/me thinks happy thoughts about (.*?)\.$": ur"/me has plenty of \1. Would you like one, %s?",
    u"^/me snaffles (.*?) off fishbot\.$": u":(",
}

#: Pre-compiled regular expressions.
compiled = []

class OneOnOne(ai.BaseOneOnOne):
    def __init__(self, identity):
        self.ident = identity

    def handle(self, message):
        if message.startswith("load module "):
            ai_str = message[12:]
            try:
                ai_class = aihandler.get_oneonone(ai_str)
            except aihandler.NoSuchAIError, e:
                self.ident.send("Failed to load module %s: %s" % (ai_str, e))
            else:
                new_ai = ai_class(self.ident)
                self.ident.set_AI(new_ai)
                self.ident.send("Great success!")
            return
        self.ident.send(u"Sorry, PMs are not (yet) supported.")

class ManyOnMany(ai.BaseManyOnMany):
    def __init__(self, room):
        if not isinstance(room, frontends.BaseGroup):
            raise TypeError, "You can only use a ManyOnMany AI for Groups."
        self.room = room

    def handle(self, message, sender):
        if message == "fishbot, part":
            self.room.leave()
            return
        elif message == "fishbot, uptime":
            diff = stats.uptimeSecs()
            self.room.send(u'Uptime: %d seconds. gnarf!' % diff)
            return
        elif message.startswith("load module "):
            ai_str = message[12:]
            try:
                ai_class = aihandler.get_manyonmany(ai_str)
            except aihandler.NoSuchAIError, e:
                self.room.send(u"Failed to load module %s: %s" % (ai_str, e))
            else:
                new_ai = ai_class(self.room)
                self.room.set_AI(new_ai)
                self.room.send(u"Great success!")
            return

        # Default:
        for regex, to in compiled:
            if regex.match(message):
                msg = regex.sub(message, to)
                if r"\1" in to:
                    var = regex.search(message)
                    msg = msg.replace(r"\1", var.group(1))
                if r"\2" in to:
                    msg = msg.replace(r"\2", str(self.room))
                try:
                    msg = msg % sender.nick
                except TypeError:
                    pass
                self.room.send(msg)
                return

def _compile_regex():
    """Compile all regular expressions and store them in a global list once."""
    global compiled
    if not compiled:
        for of, to in raw.items():
            regex = re.compile(of, re.IGNORECASE | re.UNICODE)
            compiled.append((regex, to))

_compile_regex()
