# -- coding: utf-8 --

'''functions that help formatting a string'''

import sre

def xstrip(string):
	'''cleanup a string in three steps:
1) trim whitespaces
2) remove appending dot, if the character before it wasn't a dot too
3) remove one appending whitespace if present'''
	string=string.strip()
	pattern='[^\.] ?\.$'
	result=sre.search(pattern,string)
	if result is None:
		return string
	else:
		#the beginning of the match is the end of the real data
		end=result.start()+1
		return string[:end]


def stripQM(text):
	'''return the input with the last character removed if it was a question mark'''
	if text[-1]=="?":
		return text[:-1]
	else:
		return text