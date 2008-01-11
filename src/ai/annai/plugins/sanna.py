#!/usr/bin/env python

"""Web search plugin"""

import httplib
import re
import urllib

from ai.annai.plugins import BasePlugin
import frontends 

class OneOnOnePlugin(BasePlugin):
	def __init__(self, multiorsingle):
		self.lang = u"en"
	
		self.dict = { u"en" : {"WNOTFOUND" : u"whaddayamean?",
				"WFOUND" : u"i found your article! take a look at it..",
				"WGOOGLEFOUND" : u"i guess i found your article... check it out:"}}

	def __unicode__(self):
		return u"web search plugin"

	def process(self, message, reply):
		msg = message.strip()
		func = msg.split()
		if len(func) > 1 and not func[0][0:2] is u"__":
			func = "self.%s(\"%s\")" % (func[0], message[len(func[0])+1:])
			try:
				reply = eval(func)
			except:
				pass
		return (message, reply)

	def w(self, tofind):
		"""Searches Wikipedia and returns the URI to the matching article.

		Returns the location of the article.
		"""
		# If wikipedia has found the article, the HTTP reply contains 
		# a Location: header.
		tofind = urllib.pathname2url(tofind)
		con = httplib.HTTPConnection("%s.wikipedia.org" % self.lang, 80)
		con.connect()
		con.request("GET", "/wiki/Special:Search?search=%s&go=Go" % tofind)
		location = con.getresponse().getheader("location", 1)
		con.close()

		if location != 1:
			return u"%s\n%s" % (self.dict[self.lang]["WFOUND"], location)
		# else search google: "wikipedia %s" % tofind
		con = httplib.HTTPConnection("www.google.com", 80)
		con.connect()
		con.request("GET", "/search?source=ig&hl=%s&q=wikipedia+%s" % (self.lang, tofind.replace("%20", "+")))
		str = con.getresponse().read()
		con.close()
		
		regexp = "(?<=href=\")http://%s.wikipedia.org/wiki/\S*(?=\")"
		regex = re.compile(regexp % self.lang)
		regex = regex.search(str)
		if regex != None:
			return u"%s\n%s" % (self.dict[self.lang]["WGOOGLEFOUND"], 
					regex.group(0))
		# if you haven"t found anything there too return a sad message,
		return self.dict[self.lang]["WNOTFOUND"]

class ManyOnManyPlugin(OneOnOnePlugin):
	def process(self, message, reply, sender):
		reply = OneOnOnePlugin.process(self, message, reply)[1]
		return (message, u"%s: %s" % (sender.nick, reply))

def getsite(url, toreturn = None, port = 80):
	"""Retrieves an HTTPResponse object from url.

	To reduce code repetition.
	"""
	server = url.split("/")[0]
	con = httplib.HTTPConnection(server, port)
	con.connect()
	con.request("GET", url[len(server):])
	res = con.getresponse()
	if toreturn:
		try:
			res = eval('res.' + toreturn)
		except:
			pass
	con.close()
	return res
