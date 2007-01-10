# -- coding: utf-8 --

'''functions that help formatting a string'''

import re

def xstrip( haystack ):
	'''cleanup a string in three steps:
	1) trim whitespaces
	2) remove appending dot, if the character before it wasn't a dot too
	3) remove one appending whitespace if present'''
	haystack = haystack.strip()
	pattern = r'[^\.] ?\.$'
	result = re.search( pattern, haystack )
	if result is None:
		return haystack
	else:
		#the beginning of the match is the end of the real data
		end = result.start() + 1
		return haystack[:end]


def stripQM( text ):
	'''return the input with the last character removed if it was a question mark'''
	#TODO this function looks useless. remove it?
	if text[-1] == "?":
		return text[:-1]
	else:
		return text
