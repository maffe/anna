#!/usr/bin/python
# -- coding: utf-8 --

from time import time
starttime=time()

from frontends.xmpp.connect import connect
import config

config.Misc.starttime=starttime

###start connect###
connect()
