#!/usr/bin/env python
"""Welcome to Anna, a multipurpose chatbot.
Copyright (c) 2006, 2007, 2008 Hraban Luyat.

To kill the entire chatbot, use ctrl + C.

"""
import signal
import sys
try:
    import threading as _threading
except ImportError:
    import dummy_threading as _threading
import time

import communication as c
import frontends.console
import frontends.xmpp

def discard_args(func):
    """Decorator that discards all arguments to a function."""
    def lonely_func(*args, **kwargs):
        return func()
    return lonely_func

class Anna(object):
    """The Anna bot."""
    def __init__(self):
        signal.signal(signal.SIGINT, stop)
        self.pool = []
        #self.pool.append(frontends.console.Connection())
        self.pool.append(frontends.xmpp.Connection())

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
    global bot, halt_main
    c.stderr(u"Stopping the bot...\n")
    bot.stop()
    halt_main = True

def main():
    """Start one instance of the Anna bot."""
    print __doc__
    global bot, halt_main
    c.start()
    bot = Anna()
    bot.start()
    halt_main = False
    # time.sleep() is interrupted by signals, unlike threading.Thread.join().
    while not halt_main:
        time.sleep(100)
    c.stop()

if __name__ == "__main__":
    main()
