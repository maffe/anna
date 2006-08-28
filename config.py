# -- coding: utf-8 --

import os
import sys


'''handle the configuration. .mysql{} is a list that holds mysql options. there is also .jabber and .misc . .admins[] is a list that holds all the jids with admin privileges (the owner_jid inclusive). these variables are set by .__init__()'''


'''get the data from the configuration file located at ~/.anna/config and store it in itself. see config.example for more details. if the file doesn't exist, create it and sys.exit().'''


#these values will hold the information read from the config file
mysql={}
#example: self.mysql{'host': 'localhost'}
jabber={}
#example: self.jabber{'username': 'anna'}
misc={}
#example: self.misc{'owner_jid': 'zbrovski@kroahtkscajkskkl.kqvwrkjhvvakkoaiowq09qw09ue0.666'}
admins=[] #always contains the owner_jid, even if left out in the conf file.
#example: ['fraulein@sehrschön.de','zbrovski@kroahtkscajkskkl.kqvwrkjhvvakkoaiowq09qw09ue0.666']

config_directory = os.path.expanduser('~/.anna/')
if not os.path.isdir(config_directory):
	print 'Creating personal directory: %s' % config_directory
	os.mkdir(config_directory, 0700)
config_loc = config_directory + 'config'

if not os.path.isfile(config_loc):
	create_first_conf(config_loc)
	sys.exit("edit ~/.anna/config and run this script again")

f=open(config_loc)
config_lines = f.readlines()
for line in config_lines:
	line=line.strip()
	try:
		if line[0] != '#':
			# key = val , whitespaces stripped, splitted at first '='
			try:
				(key,value)=[elem.strip() for elem in line.split('=',1)]
			except ValueError:
				sys.exit('\nthis line needs at least one "="-sign:\n\n>>> "%s"\n'%line)
			except StandardError:
				sys.exit('\nit seems there was a problem with the configuration file on this line:\n\n>>>   "%s"\n'%line)
			if key[:6].lower()=='mysql_':
				mysql[key[6:]]=value
			elif key.lower()=="jid" or key.lower()=="jabber_jid":
				(jabber['user'],jabber['server'])=value.split('@')
			elif key[:7].lower()=='jabber_':
				jabber[key[7:]]=value
			elif key.lower()=='admin_jids':
				for elem in value.split(' '):
					if elem: #prevent empty elements that occur when splitting for ex: 'a    b'
						admins.append(elem)
			elif key.lower()=='owner_jid':
				admins.append(value)
				misc[key]=value
			else:
				misc[key]=value
	except IndexError:
		pass


def create_first_conf(config_loc):
	# Create config file
	f=open(config_loc, 'w')

	#find out where the sample configuration file is
	currentdir        = os.path.abspath('.')
	script_name       = sys.argv[0]
	script_loc        = os.path.abspath(currentdir + '/' + script_name)
	script_dir        = os.path.dirname(script_loc)
	config_sample_loc = script_dir + '/config.sample'

	#copy the sample configuration to the config file
	config_sample=open(config_sample_loc)
	config_sample_str=config_sample.read()
	f.write(config_sample_str)






class Misc:
	'''miscellaneous (and usually unimportant) data/information'''

	# common highlighting characters
	hlchars=(",",":",";")

	# a list of all the muc-room instances. usually this would not be called directly but indirectly by the MucRooms class.
	rooms=[]

pass