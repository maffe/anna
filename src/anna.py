#!/usr/bin/env python
"""Welcome to Anna, a multipurpose chatbot.
Copyright (c) 2006, 2007, 2008 Hraban Luyat.

To kill the entire chatbot, use ctrl + C.

"""
USAGE = """Usage:
    $ anna FRONTEND_NAME[, ...]

"""
import imp
import signal
import sys
try:
    import threading as _threading
except ImportError:
    import dummy_threading as _threading
import time

import communication as c
import frontends

# Lock for ensuring the _import_frontends() method is only run once. Never
# .release()!
__frontends_imported = _threading.Lock()
# Dictionary of references to imported frontends.
_frontends = {}

def discard_args(func):
    """Decorator that discards all arguments to a function."""
    def lonely_func(*args, **kwargs):
        return func()
    return lonely_func

def _import_frontends(frontends):
    """Import the supplied frontends (only imports once, NOP after that)."""
    global _frontends
    if not __frontends_imported.acquire(False):
        return
    imp.acquire_lock()
    _frontends = {}
    for name in frontends:
        assert(name not in _frontends)
        mod = imp.load_module(name, *imp.find_module(name, ["frontends"]))
        _frontends[name] = mod
    imp.release_lock()

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
            if not thread.isAlive():
                return False
        return True

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
def stop():
    """Stops the bot started by L{main}."""
    global bot
    c.stderr(u"Stopping the bot...\n")
    bot.stop()

def main():
    """Start one instance of the Anna bot."""
    print __doc__
    if len(sys.argv) == 1:
        print USAGE
        sys.exit(1)
    global bot
    c.start()
    _import_frontends(sys.argv[1:])
    bot = Anna(sys.argv[1:])
    bot.start()
    # time.sleep() is interrupted by signals, unlike threading.Thread.join().
    while bot.is_running():
        time.sleep(3)
    c.stop()

if __name__ == "__main__":
    main()
else:
    _import_frontends(frontends.__all__)
