# coding: utf8

'''This plugin is for the trac of Gajim: http://trac.gajim.org'''

import urllib
import re
from xml.dom import minidom
from HTMLParser import HTMLParser

TRACURL = "http://trac.gajim.org"

def custom_error_handler(self, url, fp, errcode, errmsg, headers):
	'''Raise an IndexError when the return status isn't 200.'''
	raise IndexError
urllib.http_error_default = custom_error_handler

class MyHTMLParser( HTMLParser ):
	'''Custom HTML parser that filters out all html tags.'''

	#TODO: this is a hack.. isn't there any other way?
	result = ""

	def handle_data( self, data ):
		self.result += data

	def getResult( self ):
		x = self.result
		self.result = ""
		return x
	
	def parse( self, data ):
		'''Custom parse function that does everything - from parser.feed()
		to parser.close().'''
		self.feed( data )
		raw = self.getResult().strip()

		#rex equivalent: res = re.sub( r'\n+', '\n', raw )
		res = raw[0]
		for i in xrange( 1, len( raw ) ):
			if not ( raw[i-1] == "\n" and raw[i] == "\n" ):
				res += raw[i]

		return res

parser = MyHTMLParser()

def process( identity, message, current ):

	if not message or message[0] != "#":
		return (message, current)
	# "only use exceptions when you don't expect it to happen" - in this
	# case we expect every message starting with # to be for this plugin.
	# TODO: good or bad idea?
	try:
		if ":" in message:
			ticketid, commentid = [int(e) for e in message[1:].split( ':' )]
			text = getTicketComment( ticketid, commentid )
			uri = "%s/ticket/%s#comment:%s" % (TRACURL, ticketid, commentid)
		else:
			id = int( message[1:] )
			text = getTicketDesc( id )
			uri = "%s/ticket/%s" % (TRACURL, id)
	except ValueError:
		#if something went wrong, assume the message wasn't for this.
		return (message, current)
	except IndexError, e:
		return (message, "No such ticket/comment.")

	return (message, "%s\n- %s" % (text, uri))

def _fetchTicketXML( id ):
	'''Download the xml feed of this ticket.'''
	#TODO: prevent network time-outs from freezing the bot
	url = "%s/ticket/%s?format=rss" % (TRACURL, id)
	u = urllib.urlopen( url )
	dom = minidom.parse( u )
	u.close()
	return dom

def getTicketDesc( id ):
	'''Get the description of this ticket.'''
	dom = _fetchTicketXML( id )
	desc = dom.getElementsByTagName( "description" )[0]
	try:
		return parser.parse( desc.firstChild.data )
	except AttributeError:
		#there was no description
		return ""

def getTicketComment( ticket, comment ):
	'''Get the n-th comment for this ticket. Needless to say that this raises
	an IndexError when there is no such comment.'''
	dom = _fetchTicketXML( ticket )
	item = dom.getElementsByTagName( "item" )[ comment - 1 ]
	author = item.getElementsByTagName( "author" )[0].firstChild.data
	try:
		content = item.getElementsByTagName( "description" )[0].firstChild.data
	except AttributeError:
		#there was no content in this comment
		return "This is an empty comment."
	content = parser.parse( content )
	return "Comment %s by %s:\n%s" % ( comment, author, content )
