#!/usr/bin/env python
"""Welcome to Anna, a multipurpose chatbot.
Copyright (c) 2006, 2007, 2008 Hraban Luyat.

To kill the entire chatbot, use ctrl + C.

"""
import logging
import optparse
import signal
import sys
try:
    import threading as _threading
except ImportError:
    import dummy_threading as _threading
import time

import communication as c
import config
import frontends

USAGE = """
    $ anna [options] FRONTEND_NAME[, ...]
    $ anna --list
    $ anna --help
"""
LOGFORMAT = "%(asctime)s%(name)s: %(levelname)s: %(message)s"
LOGDATEFMT = "%c "

# Lock for ensuring the _import_frontends() method is only run once. Never
# .release()!
_frontends_imported = _threading.Lock()
# Dictionary of references to imported frontends.
_frontends = {}
# Main anna logger.
_logger = logging.getLogger("anna." + __name__)

def discard_args(func):
    """Decorator that discards all arguments to a function."""
    def lonely_func(*args, **kwargs):
        return func()
    return lonely_func

def _import_frontends(frontend_names):
    """Import the supplied frontends (only imports once, NOP after that)."""
    # No duplicates.
    assert(len(set(frontend_names)) == len(frontend_names))
    global _frontends
    if not _frontends_imported.acquire(False):
        return
    fends = __import__("frontends", globals(), locals(), frontend_names)
    _frontends = dict((n, getattr(fends, n)) for n in frontend_names)

class Anna(object):
    """The Anna bot.

    @param frontends: The frontends to load for this bot.
    @type frontends: iterator

    """
    def __init__(self, frontends):
        signal.signal(signal.SIGINT, stop)
        self.pool = []
        for name in frontends:
            self.pool.append(_frontends[name].Connection())

    def is_running(self):
        """Returns C{True} if at least one frontend is connected.

        Should only be called after calling L{start}.

        """
        for thread in self.pool:
            if thread.isAlive():
                return True
        return False

    def start(self):
        """Start all frontend threads."""
        for thread in self.pool:
            thread.connect()

    def stop(self):
        """Stop all frontend threads (and wait for them to exit)."""
        for thread in self.pool:
            thread.disconnect()
            thread.join()

@discard_args
def print_frontends():
    print "Available frontends:"
    print "\n".join("    - " + f for f in frontends.__all__)
    print
    sys.exit()

@discard_args
def stop():
    """Stops the bot started by L{main}."""
    global bot
    _logger.info("Stopping the bot...")
    bot.stop()

def main():
    """Start one instance of the Anna bot."""
    global bot
    print __doc__
    p = optparse.OptionParser(USAGE)
    p.set_defaults(loglevel=logging.WARNING)
    p.add_option("-f", "--file", help="use specified configuration file "
            "instead of default (~/.anna/config)")
    p.add_option("-l", "--list", action="callback", callback=print_frontends,
            help="print a list of available frontends")
    p.add_option("-q", "--quiet", action="store_const", const=logging.ERROR,
            dest="loglevel", help="Only report severe errors.")
    p.add_option("-v", "--verbose", action="store_const", const=logging.INFO,
            dest="loglevel", help="Report informational messages.")
    p.add_option("-d", "--debug", action="store_const", const=logging.DEBUG,
            dest="loglevel", help="Report debugging info.")
    (options, args) = p.parse_args()
    if len(args) == 0:
        p.error("You need to specify at least one frontend. See --list.")
    logging.basicConfig(level=options.loglevel, format=LOGFORMAT,
            datefmt=LOGDATEFMT)
    config.load_conf(options.file)
    c.start()
    _import_frontends(args)
    bot = Anna(args)
    bot.start()
    # time.sleep() is interrupted by signals, unlike threading.Thread.join().
    while bot.is_running():
        time.sleep(3)
    c.stop()
    _logger.info("Bot stopped.")

if __name__ == "__main__":
    main()
else:
    _import_frontends(frontends.__all__)
