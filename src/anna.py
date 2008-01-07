#!/usr/bin/env python
import signal
import sys
import threading

import communication as c
import frontends.console
import frontends.xmpp

def handle_sig(sign, frame):
    """Debug signal handler."""
    print >> sys.stderr, "SIGNAL: %r: %r" % (sign, frame)    

class Anna(object):
    """The Anna bot.

    Use the L{start} method to start the bot.

    @TODO: Handle SIGINT properly (immediately).

    """
    def __init__(self):
        signal.signal(signal.SIGINT, handle_sig)
        pool = []
        #pool.append(frontends.console.Connection())
        pool.append(frontends.xmpp.Connection())
        self.pool = pool

    def run(self):
        """This is where the main thread is until all frontend threads die."""
        for thread in self.pool:
            thread.start()
        for thread in self.pool:
            thread.join()

def main():
    c.start()
    bot = Anna()
    bot.run()
    c.stop()

if __name__ == "__main__":
    main()
