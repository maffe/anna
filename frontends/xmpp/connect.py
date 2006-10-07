# -- coding: utf-8 --
'''
connection.py
///////////////////////////////////////
Connect to the database AND to the jabber account
Define connection handlers. Get config from config file.
///////////////////////////////////////
'''

import sys
import xmpp
from socket import gethostname

from frontends.xmpp import handlers
import config

# Connect to jabber account :

def connect():
	conn=xmpp.Client(config.jabber['server'])
	conres=conn.connect()
	if not conres:
		sys.exit("Unable to connect to server %s!"%config.jabber['server'])
	if conres != 'tls':
		sys.exit("Warning: unable to estabilish secure connection - TLS failed!")
	#use hostname as resource
	hostname=gethostname().split('.',1)[0]
	authres=conn.auth(config.jabber['user'],config.jabber['password'],hostname)
	if not authres:
		sys.exit("Unable to authorize on %s - check login/password."%config.jabber['server'])
	if authres != 'sasl':
		sys.exit("Warning: unable to perform SASL auth on %s. Old authentication method used!"%config.jabber['server'])


	##  assign functions to handlers  ##

	conn.RegisterHandler('iq',handlers.version_request,typ='get',ns='jabber:iq:version')

	conn.RegisterHandler('message',handlers.joinmuc,typ='normal',ns='jabber:x:conference')
	conn.RegisterHandler('message',handlers.pm,typ='chat')
	conn.RegisterHandler('message',handlers.muc,typ='groupchat')
	#conn.RegisterHandler('message',handlers.error,'error') #fixme: make this handler

	conn.RegisterHandler('presence',handlers.subscribtion,typ='subscribe')
	conn.RegisterHandler('presence',handlers.presence)
	conn.RegisterDisconnectHandler(connect) #fixme: test if this actually makes it reconnect after disconnect


	conn.sendInitPresence(0)
	print "Bot started.\nrunning as user: %s@%s\n"%(config.jabber['user'],config.jabber['server'])

	while conn.Process(1):
		pass

	print "bot stopped"
