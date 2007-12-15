"""Conversation-party definitions for the xmpp frontend."""

import sys

import pyxmpp.all as px
import pyxmpp.jabber.all as pxj
px.jab = pxj
del pxj

from frontends import BaseIndividual, BaseGroup

class Individual(BaseIndividual):
    def __init__(self, jid, stream):
        print >> sys.stderr, "DEBUG: XMPP Individual instantiated."
        self.jid = jid
        self.stream = stream

    def __str__(self):
        return "xmpp:%s" % self.jid

    def __unicode__(self):
        return u"xmpp:%s" % unicode(self.jid)

    def get_AI(self):
        return self.ai

    def get_name(self):
        return unicode(self.jid)

    def get_type(self):
        return "xmpp"

    def set_AI(self, ai):
        self.ai = ai

    def set_name(self, name):
        self.name = name

    def send(self, message):
        message = px.Message(to_jid=self.jid, body=message,
                stanza_type="chat")
        self.stream.send(message)
