#!/usr/bin/env python
import signal
import sys
import threading

import communication as c
import frontends.console
import frontends.xmpp

def handle_sig(sign, frame):
    c.stderr("SIGNAL %r\n" % sign)
    print >> sys.stderr, ("SIGNAL %r\n" % sign)

def init():
    global pool
    pool = []
    signal.signal(signal.SIGINT, handle_sig) # DEBUG
    c.start()
    pool.append(frontends.console.Connection(name="console frontend"))

def run():
    """This is the phase that the main thread is in until all threads die."""
    for thread in pool:
        thread.start()
    for thread in pool:
        thread.join()

def cleanup():
    c.stop()

def main():
    init()
    run()
    cleanup()

if __name__ == "__main__":
    main()
