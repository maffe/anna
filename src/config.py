"""Get the data from the configuration file located at ~/.anna/config.

See config.example for more details.  If the file doesn't exist, create
it and sys.exit().  When this module is imported the configuration is
loaded and stored once so other modules can use the configuration
without having to open the file every time.  The get_conf_copy function
can be used to this end.

"""
import os
import sys
import ConfigParser

CONF_DIR = os.path.expanduser("~/.anna")
ENC = "utf8"

class AnnaConfig(object):
    """Used to communicate configuration values with other modules.

    get_conf_copy() updates this instance's __dict__ attribute and
    creates a new key for every configuartion section. For example:

    >>> c = config.get_conf_copy()
    >>> "xmpp" in dir(c)
    True
    >>> print c.xmpp
    {'password': 'secret', 'user': 'anna', 'server': 'example.net'}

    """
    def __init__(self, vals):
        self.__dict__.update(vals)

class AnnaConfigParser(object):
    """Used to parse the real configuration file.

    Parsing is done on instantiation and results are stored in the self.vals
    dictionary (which contains a key/value dictionary for each section).

    @raise ConfigParser.Error: The file is malformed.

    """
    def __init__(self, conf_loc=None):
        """Take all needed actions to complete the configuration."""
        if not conf_loc:
            conf_loc = self.get_conf_loc()
        self.vals = self.parse_conf(conf_loc)

    def create_first_conf(self, conf_loc):
        """Create a config file at the specified location."""
        # find out where the sample configuration file is (TODO: hack hack)
        conf_sample = os.path.join(os.path.pardir, 'sample.conf')

        # copy the sample configuration to the config file
        f_sample = open(conf_sample)
        f = open(conf_loc, 'w')
        f.write(f_sample.read())
        f.close()

    def get_conf_loc(self):
        """Get the location of the configuration file.

        If the file does not exist, create it and give the user instructions on
        what to do next. Returns a string. Basically this just expands
        ~/.anna/config.

        """
        if not os.path.isdir(CONF_DIR):
            print >> sys.stderr, "Creating personal directory: %s" % CONF_DIR
            os.mkdir(CONF_DIR, 0700)
        conf_loc = os.path.join(CONF_DIR, "anna.conf")
        if not os.path.isfile(conf_loc):
            self.create_first_conf(conf_loc)
            sys.exit("Edit %s and run this script again." % conf_loc)
        else:
            return conf_loc

    def get_fullpath(self, filename):
        """Get the absolute path of a config file with this name."""
        filename = os.path.expanduser(filename)
        if not os.path.isabs(filename):
            filename = os.path.join(CONF_DIR, filename)
        return filename

    def parse_conf(self, conf_loc):
        """Parse the configuration file and set the appropriate values.

        Works with new configuration files (post r136).

        """
        vals = {}
        p = ConfigParser.SafeConfigParser()
        p.read(conf_loc)
        for section in p.sections():
            vals[section] = {}
            if section == "annai_plugins":
                vals["annai_plugins"]["names"] = {}
            for (name, value) in p.items(section):
                name, value = name.decode(ENC), value.decode(ENC)
                # Hard-coded hacks.
                if section == "xmpp" and name == "jid":
                    user, node = value.split('@', 1)
                    vals["xmpp"][u"user"] = user
                    vals["xmpp"][u"server"] = node
                elif section == "misc" and name == "highlight":
                    vals["misc"]["highlight"] = list(value)
                elif section == "annai_plugins" and name.startswith("name_"):
                    vals["annai_plugins"]["names"][name[len("name_"):]] = value
                elif name == "include":
                    vals.update(self.parse_conf(self.get_fullpath(value)))
                # Normal values.
                else:
                    vals[section][name] = value
        return vals

def init(conf_loc=None):
    """Load and cache the configuration."""
    global c
    c = AnnaConfigParser(conf_loc)

def get_conf_copy():
    """Get a cached copy of the configuration."""
    n = AnnaConfig(c.vals)
    return n
