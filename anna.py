#!/usr/bin/python
# -- coding: utf-8 --

from time import time
starttime=time()

import xmpp_connect
import config

config.Misc.starttime=starttime

###start connect###
xmpp_connect.Connect()
