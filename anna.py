#!/usr/bin/python
# -- coding: utf-8 --

import time
starttime=time.time()

import connect_xmpp
import config

config.Misc.starttime=starttime

###start connect###
connect_xmpp.Connect()
