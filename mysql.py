# -- coding: utf-8 --
'''handle mysql connections'''

import MySQLdb
import sys

import config

try:
	db_r = MySQLdb.connect( user = config.mysql['user_r'],     \
												passwd = config.mysql['pass_r'],     \
												host   = config.mysql['host'],       \
												db     = config.mysql['db'],         \
												unix_socket = config.mysql['socket'],\
												port   = int( config.mysql['port'] ),\
												charset = 'utf8'                     )
except MySQLdb.OperationalError, e:
	sys.exit( e )

try:
	db_w = MySQLdb.connect( user = config.mysql['user_w'],     \
												passwd = config.mysql['pass_w'],     \
												host   = config.mysql['host'],       \
												db     = config.mysql['db'],         \
												unix_socket = config.mysql['socket'],\
												port   = int( config.mysql['port'] ),\
												charset = 'utf8'                     )
except MySQLdb.OperationalError, e:
	sys.exit( e )