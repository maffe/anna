#!/usr/bin/python
# -- coding: utf-8 --

from time import time
starttime=time()

import connect_xmpp
import config

config.Misc.starttime=starttime

###start connect###
connect_xmpp.Connect()
