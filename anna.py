#!/usr/bin/python
# -- coding: utf-8 --

import time
starttime=time.time()

import connection
import config

config.Misc.starttime=starttime

###start connect###
connection.Connect()
