# coding: utf8

'''This plugin is for the trac of Gajim: http://trac.gajim.org'''

import urllib
import re
from xml.dom import minidom

TRACURL = "http://trac.gajim.org"

def custom_error_handler(self, url, fp, errcode, errmsg, headers):
	'''Raise an IndexError when the return status isn't 200.'''
	raise IndexError
urllib.http_error_default = custom_error_handler

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
		return (message, current)
	except IndexError, e:
		return ( message, "No such ticket/comment." )

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
	return desc.firstChild.data

def getTicketComment( ticket, comment ):
	'''Get the n-th comment for this ticket. Needless to say that this raises
	an IndexError when there is no such comment.'''
	dom = _fetchTicketXML( ticket )
	item = dom.getElementsByTagName( "item" )[ comment - 1 ]
	author = item.getElementsByTagName( "author" )[0].firstChild.data
	content = item.getElementsByTagName( "description" )[0].firstChild.data
	return "Comment %s by %s:\n%s" % ( comment, author, content.strip() )

#def getTicket( id ):
#	'''Return information about this ticket.'''
	
