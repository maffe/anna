"""Tools for safe inter-thread operations.

Before using the L{stdout} and L{stderr} functions make sure to call
L{start}. If you call that function, don't forget to call L{stop} before
exiting your program to kill the two threads polling for messages.

"""
import getpass as _getpass_mod
import logging
import mutex
try:
    import readline
except:
    pass
import sys
try:
    import threading as _threading
except ImportError:
    import dummy_threading as _threading
import Queue

# The lock for the stdout.
_lock = _threading.RLock()
_logger = logging.getLogger("anna." + __name__)
#: Whether or not the stderr should wait for the stdout.
combined_out_err = True

class _PrintPoller(_threading.Thread):
    """Print all messages in a queue to given stream as soon as possible.

    Adding None to the stdout queue kills the thread.

    @param stream: The stream to print the messages to.
    @type stream: A file-like object.
    @param name: The textual representation of the stream.
    @type name: C{unicode} or C{str}
    @TODO: do not quit on exceptions but print nice traceback.

    """
    def __init__(self, stream, name):
        _threading.Thread.__init__(self)
        self.name = name
        self.queue = Queue.Queue()
        self.stream = stream

    def run(self):
        while 1:
            # Queue.Queue.get() is blocking.
            msg = self.queue.get()
            # Test for exit-condition:
            if msg is None:
                return
            _lock.acquire()
            try:
                try:
                    self.stream.write(msg)
                    self.stream.flush()
                except:
                    print >> sys.stderr, "ERROR:", self.name, "queue halted"
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

class TimedMutex(mutex.mutex):
    """A mutex that unlocks itself after a given amount of seconds.

    This class can be used to moderate the interval at which all threads
    combined can use a certain resource.

    >>> import time
    >>> m = TimedMutex(5)
    >>> m.testandset()
    True
    >>> m.testandset()
    False
    >>> time.sleep(6)
    >>> m.testandset()
    True

    @param timeout: Seconds to wait before unlocking.
    @type timeout: C{int}
    @TODO: Support bursts (so 3 quickly is fine, but not 4, for example).

    """
    def __init__(self, timeout):
        mutex.mutex.__init__(self)
        self.timeout = timeout

    def __repr__(self):
        return "<TimedMutex(%d)>" % self.timeout

    def testandset(self):
        if mutex.mutex.testandset(self):
            _threading.Timer(self.timeout, mutex.mutex.unlock, [self]).start()
            return True
        else:
            return False

def stdout(msg, encoding=None):
    """Print given message to stdout in a thread-safe non-blocking way.

    If the message is a unicode object the proper encoding is determined in the
    following order:
        1. The supplied encoding.
        2. The auto-detected encoding of stdout, if available.
        3. Defaults to UTF-8.
    Characters that can not be encoded are replaced by question marks.

    If another thread is either printing or waiting for input this message will
    wait until that thread is finished.  The message will be placed in a(n
    infinite) buffer.

    Do not forget to call L{start} before using this function. Call L{stop}
    when you are done.

    @param msg: The message to print to stdout.
    @type msg: C{str} or C{unicode}

    """
    if isinstance(msg, unicode):
        msg = _encode(msg, encoding)
    _logger.warning("Passing non-unicode object to stdout().")
    _poller_out.queue.put(msg)

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
        _poller_err.queue.put(msg)
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

def _banner(msg, encoding, func):
    """Assert given function is executed right after given message is printed.

    This is useful for prompts like C{raw_input} and C{getpass.getpass}.
    Returns the return value of given function. The return value must be a
    C{str} and will be decoded using given encoding. The given message will
    also be encoded with this encoding if it is a C{str} instead of a
    C{unicode} object. Given args and kwargs are supplied to the function
    as arguments if the C{func} argument is a tuple.

    @param func: Function to call or tuple containing three elements:
        0. The function to call.
        1. The arguments.
        2. The keyword arguments.
    @type func: iterator or callable

    """
    if isinstance(msg, unicode):
        msg = _encode(msg, encoding)
    _lock.acquire()
    try:
        sys.stdout.write(msg)
        sys.stdout.flush()
        if callable(func):
            val = func()
        else:
            val = func[0](*func[1], **func[2])
    finally:
        _lock.release()
    if encoding is not None:
        return val.decode(encoding, "replace")
    else:
        try:
            return val.decode(sys.stdin.encoding, "replace")
        except TypeError:
            # sys.stdin.encoding is None; not auto-detected.
            return val.decode("utf-8", "replace")

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
    L{stdout_block} instead of L{stdout}. Note that that only ensures it is
    printed somewhere before the prompt, not that nothing will be printed
    between both calls, while passing a message I{does} ensure nothing is
    printed in between.

    @return: User-provided value.
    @rtype: C{unicode}
    @raise EOFError: The user hits Ctrl-D.

    """
    return _banner(msg, encoding, raw_input)

def getpass(msg, encoding=None):
    """Like L{stdin} but for C{getpass.getpass} instead of C{raw_input}."""
    return _banner(msg, encoding, (_getpass_mod.getpass, (), dict(prompt="")))

def start():
    """Use this function to initiate the connection polling.

    Do NOT use the non-blocking functions (i.e.; L{stdout} and L{stderr})
    before calling this function.

    """
    # Start polling for messages to print to stdout/stderr in a seperate thread.
    global _poller_out, _poller_err
    _poller_out = _PrintPoller(sys.stdout, "stdout")
    _poller_err = _PrintPoller(sys.stderr, "stderr")
    # Daemons exit when the main thread exits.
    _poller_out.setDaemon(True)
    _poller_err.setDaemon(True)
    _poller_out.start()
    _poller_err.start()

def stop():
    """Cleanup function that stops all running pollers."""
    global _poller_out, _poller_err
    _poller_out.queue.put(None)
    _poller_err.queue.put(None)
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
