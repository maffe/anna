# -- coding: utf-8 --
'''connection.py

Connect to the jabber account. Define connection handlers. Get config
from config file.'''

import sys
import xmpp
import socket
import threading

import frontends.xmpp as xmpp_frontend
import frontends.xmpp.handlers as handlers
import config


class ConnectThread( threading.Thread ):
	'''A thread to start the xmpp connection. these docs are from the old function:
connect to a jabber server with the credentials specified in the
configuration file. this function goes into a loop that only ends when a
disconnection from theserver is detected. this detection is done by the
xmpppy python module and it seems it isn't very efficient... for me at
least; every few days the bot disconnects from the server for no appearant
reason and just doesn't die. even with the automatic reconnect on
disconnection... in other words: BIG #TODO'''
	def __init__( self ):
		threading.Thread.__init__( self )

	def run( self ):
		'''connect to the jabber server as specified in the configuration. quits if the
connection is insecure, loops infinitely until a disconnection is detected.
TODO: more flexible debugging and non-secure connection establishment.'''
		conn = xmpp.Client( config.jabber['server'] )
		#copy the reference to the connection object to the parent module (__init__.py)
		#before doing anything else because much functions depend on this:
		xmpp_frontend.conn = conn
		conres = conn.connect()
		if not conres:
			sys.exit( "Unable to connect to server %s!" % config.jabber['server'] )
		if conres != 'tls':
			sys.exit( "Warning: unable to estabilish secure connection - TLS failed!" )
		#use hostname as resource
		resource = socket.gethostname().split( '.', 1 )[0]
		authres = conn.auth( config.jabber['user'],
		                     config.jabber['password'], resource )
		if not authres:
			sys.exit(
				"Unable to authorize on %s - check login/password."
				% config.jabber['server']
			)
		
		if authres != 'sasl':
			sys.exit(
				"Warning: unable to perform SASL auth on %s. Old authentication method used!"
				% config.jabber['server']
			)
		
		##  assign functions to handlers  ##
		
		conn.RegisterHandler( 'iq', handlers.version_request,
		                      typ = 'get', ns = 'jabber:iq:version' )
		conn.RegisterHandler( 'message', handlers.joinmuc,
		                      typ = 'normal', ns = 'jabber:x:conference' )
		conn.RegisterHandler( 'message', handlers.pm, typ = 'chat' )
		conn.RegisterHandler( 'message', handlers.muc, typ = 'groupchat' )
		#conn.RegisterHandler('message',handlers.error,'error')
		#TODO: make this handler
		
		conn.RegisterHandler( 'presence', handlers.subscribtion, typ = 'subscribe' )
		conn.RegisterHandler( 'presence', handlers.presence )
		#conn.RegisterDisconnectHandler( connect )
		#TODO: test if this actually makes it reconnect after disconnect
		
		#send online presence
		conn.sendInitPresence( 0 )
		print "XMPP frontend started: %(user)s@%(server)s" % config.jabber
		while conn.Process( 1 ):
			pass

print "XMPP frontend for user %(user)s@%(server)s has ended." % config.jabber