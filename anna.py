#!/usr/bin/python
# -- coding: utf-8 --

from time import time
import stats
stats.starttime = time()
import sys
import frontends.xmpp.connection as xmpp
import frontends.console.connection as console

#TODO: find a way to run multiple frontends simultaneously AND stably
if __name__ == "__main__":
	#console.connect()
	xmpp.connect()
