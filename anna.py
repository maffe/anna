#!/usr/bin/python
# -- coding: utf-8 --

from time import time
import stats
stats.starttime = time()
import sys
import frontends.xmpp.connection as xmpp
import frontends.console.connection as console

###start connect###
xmppThread = xmpp.ConnectThread()
xmppThread.start()
#consoleThread = console.ConnectThread()
#consoleThread.start()

print >> sys.stderr, "threads started succesfully. program will", \
	"end when all threads have ended."
