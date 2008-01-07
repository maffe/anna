"""Handle operations on std(in/out/err) in a thread-safe way.

Before using the L{stdout} and L{stderr} functions make sure to call
L{start}. If you call that function, don't forget to call L{stop} before
exiting your program to kill the two threads polling for messages.

"""
import sys
try:
    import threading as _threading
except ImportError:
    import dummy_threading as _threading
import Queue

# The lock for the stdout.
_lock = _threading.RLock()
#: Whether or not the stderr should wait for the stdout.
combined_out_err = True

class _PollerStdout(_threading.Thread):
    def run(self):
        """Print all messages in the stdout queue as soon as possible.

        Adding None to the stdout queue kills the thread.

        @TODO: do not quit on exceptions but print nice traceback.

        """
        global _stdout_q
        while 1:
            msg = _stdout_q.get()
            if msg is None:
                return
            _lock.acquire()
            try:
                try:
                    sys.stdout.write(msg)
                    sys.stdout.flush()
                except:
                    print >> sys.stderr, "ERROR: stdout queue halted"
                    # The system is fubar now anyway, better delete the queue and
                    # die than risk the calling function catching this exception
                    # somehow and continuing to pump messages in the queue.
                    del _stdout_q
                    raise
            finally:
                _lock.release()

class _PollerStderr(_threading.Thread):
    def run(self):
        global _stderr_q
        while 1:
            msg = _stderr_q.get()
            if msg is None:
                return
            _lock.acquire()
            try:
                try:
                    sys.stderr.write(msg)
                    sys.stderr.flush()
                except:
                    print >> sys.stderr, "ERROR: stderr queue halted"
                    del _stderr_q
                    raise
            finally:
                _lock.release()

def _encode(msg, encoding):
    """Decode a message for printing to stdout 'coute-que-coute'."""
    if __debug__:
        if not isinstance(msg, unicode):
            raise TypeError, "Message must be a unicode object."
    if encoding is not None:
        return msg.encode(encoding, "replace")
    else:
        try:
            return msg.encode(sys.stdout.encoding, "replace")
        except TypeError:
            return msg.encode("utf-8", "replace")

def stdout(msg, encoding=None):
    """Print given message to stdout in a thread-safe non-blocking way.

    If the message is a unicode object the proper encoding is determined in the
    following order:
        1. The supplied encoding.
        2. The auto-detected encoding of stdin, if available.
        3. Defaults to UTF-8.
    Characters that can not be encoded are replaced by question marks.

    If another thread is either printing or waiting for input this message will
    wait until that thread is finished.  The message will be placed in a(n
    infinite) buffer.

    @param msg: The message to print to stdout.
    @type msg: C{string} or C{unicode}

    """
    if isinstance(msg, unicode):
        msg = _encode(msg, encoding)
    elif __debug__:
        stderr(u"WARNING: passing non-unicode object to stdout().")
    _stdout_q.put(msg)

def stdout_block(msg, encoding=None):
    """Like L{stdout} except that it blocks until the message is printed."""
    if isinstance(msg, unicode):
        msg = _encode(msg, encoding)
    _lock.acquire()
    try:
        sys.stdout.write(msg)
        sys.stdout.flush()
    finally:
        _lock.release()

def stderr(msg, encoding=None):
    """Same as L{stdout} but for stderr.

    Note that if no encoding is supplied stdin's encoding is used for
    auto-detection.  If stderr is not at some point redirected to stdout this
    function is useless (and actually works adversely).

    @TODO: Make option to unlock stderr available through config or similar.

    """
    if isinstance(msg, unicode):
        msg = _encode(msg, encoding)
    if combined_out_err:
        _stderr_q.put(msg)
    else:
        sys.stderr.write(msg)
        sys.stderr.flush()

def stderr_block(msg, encoding=None):
    """Like L{stdout_block} but for stderr."""
    if isinstance(msg, unicode):
        msg = _encode(msg, encoding)
    if combined_out_err:
        _lock.acquire()
        try:
            sys.stderr.write(msg)
            sys.stderr.flush()
        finally:
            _lock.release()
    else:
        sys.stderr.write(msg)
        sys.stderr.flush()

def stdin(msg, encoding=None):
    """Thread-safe implementation of raw_input() using stdout.

    Works like L{stdout} for output.  Determines the encoding to use for
    decoding the obtained message in the same way.  Invalid characters are
    replaced by question marks.

    Note that if you absolutely want a certain message to appear before the
    prompt it is very important you pass it as an argument here instead of
    printing it with L{stdout}. That function is threaded and uses a message
    queue for delivering output while this function does not. The only other
    way of making sure your prompt is printed before this one is by using
    L{stdout_block} instead of L{stdout}.

    @return: User-provided value.
    @rtype: C{unicode}
    @raise EOFError: The user hits Ctrl-D.

    """
    if isinstance(msg, unicode):
        msg = _encode(msg, encoding)
    _lock.acquire()
    try:
        sys.stdout.write(msg)
        sys.stdout.flush()
        val = raw_input()
    finally:
        _lock.release()
    if encoding is not None:
        return val.decode(encoding, "replace")
    else:
        try:
            return val.decode(sys.stdin.encoding, "replace")
        except ValueError:
            return val.decode("utf-8", "replace")

def start():
    """Use this function to initiate the connection polling.

    Do NOT use the non-blocking functions (i.e.; L{stdout} and L{stderr})
    before calling this function.

    """
    # Start polling for messages to print to stdout/stderr in a seperate thread.
    global _poller_out, _poller_err, _stdout_q, _stderr_q
    _stdout_q = Queue.Queue()
    _stderr_q = Queue.Queue()
    _poller_out = _PollerStdout()
    _poller_err = _PollerStderr()
    _poller_out.setDaemon(False)
    _poller_err.setDaemon(False)
    _poller_out.start()
    _poller_err.start()

def stop():
    """Cleanup function that stops all running pollers."""
    global _poller_out, _poller_err
    _stdout_q.put(None)
    _stderr_q.put(None)
    _poller_out.join()
    _poller_err.join()
    del _poller_out, _poller_err

def test():
    print "If you see tests a through f (in no particular order) when the \
program finishes everything works."
    start()
    stdout(u"a. Testing non-blocking stdout.\n")
    stderr(u"b. Testing non-blocking stderr.\n")
    stdout_block(u"c. Testing blocking stdout.\n")
    stderr_block(u"d. Testing blocking stderr.\n")
    stdout(u"f. You entered: %s\n" % stdin("e. Please enter a string >>> "))
    stop()

if __name__ == "__main__":
    test()
    sys.exit()
