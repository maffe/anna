"""Plugin that corrects dutch grammar.
"""
import re

from ai.annai.plugins import BasePlugin
import communication as c
import frontends
import random

def is_cp(word):
    return len(word) > 3 and word.endswith("er") and (word[-3] != "e" or word == "meer")

def is_vnw(word):
    return word in ["dat", "wat"]

def is_znid(word):
    return word in ["de", "het", "een", "die", "deze", "enkele", "dat"]

def is_als(word):
    return word == 'als'

def apply_pattern(pattern, words):
    ptrns = pattern.split(",")
    ids = [compile_pattern(p) for p in ptrns]
    i = j = 0
    while i < len(words):
        if j >= len(ids):
            return words[0]
        # execute pattern
        if not ids[j][0] == "?" and idfuncs["is_" + ids[j][0]](words[i]) == ids[j][1]:
            return False
        a = ids[j][2] - 1
        while a > 0:
            i += 1
            if i >= len(words):
                return False

            if j + 1 < len(ids) and not idfuncs["is_" + ids[j + 1][0]](words[i]) == ids[j + 1][1]:
                j += 1
                break
            if not ids[j][0] == "?" and idfuncs["is_" + ids[j][0]](words[i]) == ids[j][1]:
                return False
            a -= 1
        i += 1
        j += 1
    return False

def compile_pattern(pattern):
    inv = pattern[0] == "!"
    amount = int(pattern[pattern.find("+") + 1:]) if "+" in pattern else 1
    pat = pattern[1:] if inv else pattern
    pat = pat[:pat.find("+")] if "+" in pat else pat
    return (pat, inv, amount)

class _Plugin(BasePlugin):
    """Plugin compatible with ManyOnMany and OneOnOne API."""
    #: Regular expression used to search for dump requests.
    rex = re.compile(r"\bals\b")
    ws = re.compile(r"\w+")
    wrong = ["!znid,cp,als", "!znid,cp,!vnw+4,als", "!znid,cp,znid,?+2,als"]
    def __init__(self, party, args):
        self.party = party

    def __unicode__(self):
        return u"granna plugin"

    def process(self, message, reply, *args, **kwargs):
        words = self.ws.findall(message.lower())

        # correct 'als dan'
        res = self.rex.search(message.lower())
        if not res is None:
            i = words.index('als')
            if not i == None:
                for i in xrange(len(words)):
                    for pattern in self.wrong:
                        if apply_pattern(pattern, words[i:]):
                            reply = message[0:res.start()] + "DAN" + message[res.end():]
                            return (message, "Wrong! '" + reply + "'")
        
        # Test misspelled words
        for word in words:
            if word in miss:
                return (message, miss[word] + " you " + random.choice(ss))
        return (message, reply) 

OneOnOnePlugin = _Plugin
ManyOnManyPlugin = _Plugin
idfuncs = dict(x for x in locals().iteritems() 
    if callable(x[1]) and x[0].startswith("is_"))

miss = {"overnieuw":u"opnieuw", "interesant":"interessant", "eigelijk":"eigenlijk"}
ss = [u"dumbass", u"asshole", u"noob"]

import pprint
