#!/usr/bin/python
# vim:fileencoding=utf-8
#all files are written with ts=2 and 80 characters screen-width:
################################################################################

from time import time
import stats
stats.starttime = time()
import sys
#import frontends.xmpp.connection as frontend
import frontends.console.connection as frontend

#TODO: find a way to run multiple frontends simultaneously AND stably
if __name__ == "__main__":
	frontend.connect()
