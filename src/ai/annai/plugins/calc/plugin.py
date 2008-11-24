'''Annai wrapper for the calculator library.

Only reacts when the expression can be succesfully parsed. Acts shy (only
reacts when no other plugin reacted yet).

'''
import logging
try:
    import threading as _threading
except ImportError:
    import dummy_threading as _threading
import Queue

import processing

from ai.annai.plugins import BasePlugin

import calc

_logger = logging.getLogger('anna.' + __name__)
_setuplock = _threading.Lock()
_jobqlock = _threading.Lock()
_manager = None
_jobq = None

def work(inq, outq):
    '''Consume jobs from the queue and report the answer to given handler.'''
    pars = calc.MyParser()
    _logger.debug("Worker instantiated.")
    while 1:
        try:
            (success, result) = pars.parse(inq.get())
            _logger.debug("Worker completed job.")
        except ArithmeticError, e:
            outq.put((False, u'Error: %s' % (e,)))
        else:
            outq.put((success, u'%g' % result))

class Manager(_threading.Thread):
    '''Manage worker processes, spawn new ones when needed and kill rogues.

    Kills processes that take longer than given timeout in seconds to respond.

    '''
    def __init__(self, jobqueue, timeout=2, *args, **kwargs):
        _threading.Thread.__init__(self, *args, **kwargs)
        self.timeout = timeout
        self.setup_workers()
        self.jobq = jobqueue

    def setup_workers(self):
        self.inq = processing.Queue()
        self.outq = processing.Queue()
        self.worker = processing.Process(target=work, args=[self.outq,
                self.inq], name='Annai calc plugin worker')
        _logger.debug('Started new process %s.', self.worker.getName())
        self.worker.setDaemon(True)
        self.worker.start()

    def take_job(self):
        '''Listen for incoming job and delegate to worker process.'''
        _logger.debug('%s waiting for job...', self)
        jobt = self.jobq.get()
        _logger.debug('Got job %s, passing on to worker.', jobt)
        (job, callback, highlight) = jobt
        # There can not be communication yet.
        assert(self.inq.empty() and self.outq.empty())
        self.outq.put(job)
        try:
            (success, res) = self.inq.get(timeout=self.timeout)
        except Queue.Empty:
            self.worker.terminate()
            _logger.debug('%s reached timeout on job %s, killed.',
                    self.worker.getName(), jobt)
            # The process can have completed between the get() and this
            # exception handling, in which case it will have written to the
            # queue. That must be flushed:
            if not self.inq.empty():
                self.inq.get()
            self.setup_workers()
            (success, res) = (False, u'Error: computation took too long'
                                    ' (> %d seconds). Aborted.' % self.timeout)
        if success or (highlight and res.lower().startswith('error')):
            callback(res)
        # There can not be communication left.
        assert(self.inq.empty() and self.outq.empty())

    def run(self):
        while 1:
            self.take_job()

class _Plugin(BasePlugin):
    def __init__(self, party, args):
        self.party = party

    def __str__(self):
        return 'calc plugin'

    def __unicode__(self):
        return u'calc plugin'

    def process(self, message, reply, sender=None, highlight=True):
        '''Solve a arithmetic problem.

        Only report errors if highlighted.

        '''
        if reply is None:
            _logger.debug(u'Delegating job to %s.', _manager.getName())
            _jobq.put((message, self.party.send, highlight))
            _logger.debug(u'Succesfully delegated job.')
        return (message, reply)

OneOnOnePlugin = _Plugin
ManyOnManyPlugin = _Plugin

def setup_manager():
    global _setuplock, _manager, _jobq
    if not _setuplock.acquire(False):
        # Manager already instantiated.
        return
    _jobq = Queue.Queue(0)
    # The manager is a thread that communicates with the worker process.
    _manager = Manager(_jobq)
    _manager.setDaemon(True)
    _manager.start()

setup_manager()
