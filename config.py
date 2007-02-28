"""Handle the configuration.

.mysql{} is a list that holds mysql options.  There is also .jabber and .misc .
.admins[] is a list that holds all the jids with admin privileges (the
owner_jid inclusive).  These variables are set by .__init__()

"""
"""Get the data from the configuration file located at ~/.anna/config.

See config.example for more details.  If the file doesn't exist, create it and
sys.exit().

"""
import os
import sys
import ConfigParser

# These values will hold the information read from the config file.
mysql = {}
# Example: self.mysql{'host': 'localhost'}
jabber = {}
# Example: self.jabber{'username': 'anna'}
misc = {}
# Example: self.misc{'owner_jid': 'zbrovski@kl.kq'}
admins = []
# Example: ['fraulein@sehrschon.de','zbrovski@kl.kq']. Always contains the
# owner_jid, even if left out in the conf file.

def main():
	"""Take all needed actions to complete the configuration."""
	configLoc = getConfigLoc()
	# Determine whether this is old or new style config by checking if the file
	# is malformed. This is not very good (if it /is/ new-style but simply
	# wrong) this will produce odd results. Backwards compatibility will
	# disappear after a while.
	p = ConfigParser.SafeConfigParser()
	try:
		p.read(configLoc)
		parseConfig(configLoc)
	except ConfigParser.MissingSectionHeaderError:
		parseConfigOld(configLoc)
		migrateConf(configLoc)

def createFirstConf(configLoc):
	"""Create a config file at the specified location."""
	f = open(configLoc, 'w')

	#find out where the sample configuration file is
	currentDir       = os.path.abspath('.')
	scriptName       = sys.argv[0]
	scriptLoc        = os.path.abspath('/'.join((currentDir, scriptName)))
	scriptDir        = os.path.dirname(scriptLoc)
	configSampleLoc  = '/'.join((scriptDir, 'config.sample'))

	#copy the sample configuration to the config file
	configSample = open(configSampleSoc)
	configSampleStr = configSample.read()
	f.write(configSampleStr)
	f.close()

def getConfigLoc():
	"""Get the location of the configuration file.

	If the file does not exist, create it and give the user instructions on what
	to do next.  Returns a string.

	"""
	configDirectory = os.path.expanduser("~/.anna")
	if not os.path.isdir(configDirectory):
		print >> sys.stderr, "Creating personal directory: %s" % configDirectory
		os.mkdir(configDirectory, 0700)
	configLoc = '/'.join((configDirectory, "config"))
	if not os.path.isfile(configLoc):
		createFirstConf(configLoc)
		sys.exit("Edit %s and run this script again." % configLoc)
	return configLoc

def parseConfig(configLoc):
	"""Parse the configuration file and set the appropriate values.

	Works with new configuration files (post r136).

	"""
	p = ConfigParser.SafeConfigParser()
	p.read(configLoc)
	for (name, value) in p.items("jabber"):
		if name == "jid":
			(jabber['user'], jabber['server']) = value.split('@')
		else:
			jabber[name] = value
	for (name, value) in p.items("mysql"):
		mysql[name] = value
	for (name, value) in p.items("misc"):
		if name == "admin_jids":
			for elem in value.split():
				admins.append(elem)
		elif name == "owner_jid":
			admins.append(value)
			misc[name] = value
		else:
			misc[name] = value

# Functions for backwards compatibility:

def migrateConf(loc):
	"""Migrate the configuration from file at given location to a new syntax.

	This function will rename the old file (append ".old" to it) and create a
	new version saved under its previous name.

	"""
	p = ConfigParser.SafeConfigParser()
	os.rename(loc, "%s.old" % loc)

	p.add_section("jabber")
	for (option, value) in jabber.iteritems():
		p.set("jabber", option, value)
	p.add_section("mysql")
	for (option, value) in mysql.iteritems():
		p.set("mysql", option, value)
	p.add_section("misc")
	for (option, value) in misc.iteritems():
		p.set("misc", option, value)
	
	f = open(loc, 'w')
	p.write(f)
	f.close()
	print >> sys.stderr, "NOTICE: Updated config file %s." % loc

def parseConfigOld(configLoc):
	"""Old and deprecated way to parse the configuration file.

	Only works on old-style conf files (that is; pre-r136 config.sample files).

	"""
	f = open(configLoc)
	config_lines = f.readlines()

	for line in config_lines:
		line = line.strip()
		try:
			if line[0] != '#':
				# key = val , whitespaces stripped, splitted at first '='
				try:
					(key, value) = [elem.strip() for elem in line.split('=', 1)]
				except ValueError:
					sys.exit('\nThis line needs at least one "="-sign:\n\n>>> "%s"\n' % line)
				except StandardError:
					sys.exit('\nIt seems there was a problem with the configuration file on this line:\n\n>>>   "%s"\n' % line )
	
				if key[:6].lower() == 'mysql_':
					mysql[key[6:]] = value
				elif key.lower() == "jid" or key.lower() == "jabber_jid":
					(jabber['user'], jabber['server']) = value.split('@')
				elif key[:7].lower()== 'jabber_':
					jabber[key[7:]] = value
				elif key.lower() == 'admin_jids':
					for elem in value.split(' '):
						if elem: #prevent empty elements that occur when splitting for ex: 'a    b'
							admins.append(elem)
				elif key.lower() == 'owner_jid':
					admins.append(value)
					misc[key] = value
				else:
					misc[key] = value
	
		except IndexError:
			pass
	
	f.close()

class Misc:
	"""Miscellaneous (and usually unimportant) data/information."""
	# TODO: this is some ancient code, from back in the days... ToRemove.
	# common highlighting characters
	hlchars = (",", ":", ";")

main()
