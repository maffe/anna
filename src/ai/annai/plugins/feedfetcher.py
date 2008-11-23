"""Plugin that fetches and interprets news feeds.

@TODO: Currently only supports the atom 1.0 spefication.

"""
import itertools
import logging
import re
try:
    import threading as _threading
except ImportError:
    import dummy_threading as _threading
import time
import urllib2

import feedparser
import html2text
from BeautifulSoup import BeautifulSoup

import ai.annai
from ai.annai.plugins import BasePlugin, PluginError
import frontends

#: Default interval between feed checks in seconds.
DEFAULT_INTERVAL = 5
HTML_TYPES = ("html", "xhtml", "text/html", "application/xhtml+xml")
MIN_INTERVAL = 60
#: Maximum number of concurrent running plugins overall.
MAX_CONCURRENT_THREADS = 10
FORMAT = u"""== %(title)s (%(date)s) ==

%(content)s

- <%(url)s>"""

_logger = logging.getLogger("anna." + __name__)
#: Semaphore for keeping track of concurrent feedfetcher threads.
_tickets = _threading.Semaphore(MAX_CONCURRENT_THREADS)
_nos_rex = re.compile(r"https?://(?:[\-\w\.]*\.)?nos\.nl/")

def _parse_nos(entry):
    """Extracts the article from a nos.nl link in Markdown form.
    
    @TODO: Catch exceptions.
    
    """
    if not (hasattr(entry, "link") and _nos_rex.match(entry["link"])):
        return None
    art = BeautifulSoup(urllib2.urlopen(entry["link"])).find(id="tt_article")
    # Remove all useless children.
    art.find("div", "ext-links").extract()
    art.find("div", "readspeaker").extract()
    art.find("img", "tt_bullet").extract()
    return html2text.html2text(unicode(art))

def _parse_all(entry):
    """Unpacks an atom entry as parsed by feedparser to a more concise object.

    If the entry can not be processed for some reason (like unknown encoding)
    C{None} is returned. Favours entries of type text/plain. If there is no
    content with type text/plain the last content dictionary in the list is
    used.

    @return: A unicode object ready to be printed to the user.
    @rtype: C{unicode} or C{None}

    """
    try:
        # Feedparser always decodes to GMT.
        date = "%s UTC" % time.asctime(entry["updated_parsed"])
    except KeyError:
        return None
    if "content" not in entry:
        # If there's no content, try the summary.
        try:
            content = entry["summary_detail"]["value"]
        except KeyError:
            return None
        if entry["summary_detail"]["type"] in HTML_TYPES:
            content = html2text.html2text(content)
    else:
        content = None
        for dic in entry["content"]:
            if dic["type"] in ("text", "text/plain"):
                # If there is a plaintext entry, use that.
                content = dic["value"]
                break
            elif dic["type"] in HTML_TYPES:
                # HTML is second choice.
                #:TODO: What can dic["value"] contain, here? Always unicode?
                content = html2text.html2text(dic["value"])
    title = entry.get("title", u"No title")
    url = entry.get("link", u"...")
    # If there was none, default to the last-supplied content.
    # Now check if all elements are unicode objects.
    if isinstance(title, unicode) and isinstance(url, unicode) \
            and isinstance(content, unicode):
        return FORMAT % locals()
    else:
        return None

class _Plugin(BasePlugin):
    """Will only instantiate if there is room for another thread.

    Make sure to always call the L{stop} method or delete all references to an
    instance of this class after instantiating it succesfully to prevent
    "zombie" threads from consuming thread tickets.

    """
    def __init__(self, party, args):
        # If this is not None, process() will raise a PluginError exception
        # with this message.
        self.error = None
        if len(args) != 1:
            raise PluginError, u"Usage: load plugin feedparser <feed-url>"
        if _tickets.acquire(blocking=False) == False:
            raise PluginError, u"Sorry, this plugin is over-used."
        self.feed_url = args[0]
        self.party = party
        self.prefix = "news "
        # Seconds between updates.
        self.update_interval = DEFAULT_INTERVAL
        self.timer = _threading.Timer(0, self._check_feed)
        self.timer.start()

    def __unicode__(self):
        return u"feed parser plugin for <%s>" % self.feed_url

    def _check_feed(self):
        """Check the news feed and take action depending on updates.
        
        @TODO: Format-independent parsing.
        @TODO: Support 'un-wellformed' XML.
        
        """
        if self.error is not None:
            return
        _logger.debug(u"Feedfetcher: checking %s.", self.feed_url)
        # If this function was not called by the timer it's still running.
        self.timer.cancel()
        d = feedparser.parse(self.feed_url)
#         if d["bozo"]:
#             self._stop(u"parsing feed failed, plugin can not continue.")
#             return
#         if not d["version"] == "atom10":
#             self._stop(u"Only atom 1.0 is supported for now.")
#             return
        new_entries = []
        for entry in d["entries"]:
            try:
                # Get the result of the first parser that does not return None.
                parsed = itertools.dropwhile(lambda x: x is None, (p(entry) for
                    p in _parsers)).next()
            except StopIteration:
                _logger.info(u"Incompatible feed entry: %s.", entry)
                continue
            try:
                if entry["updated_parsed"] <= self.latest_elem:
                    _logger.debug("%r <= %r", entry["updated_parsed"],
                            self.latest_elem)
                    # This element is not newer than the element we saw last
                    # time. The entries are expected to be ordered
                    # chronologically.
                    break
                else:
                    _logger.debug("%r > %r", entry["updated_parsed"],
                            self.latest_elem)
            except AttributeError:
                # There is no self.latest_elem: this is the first fetch.
                #:TODO: This belongs in a seperate routine.
                self.latest_elem = entry["updated_parsed"]
                self.timer = _threading.Timer(self.update_interval,
                                                        self._check_feed)
                self.timer.setDaemon(True)
                self.timer.start()
                return
            new_entries.append(parsed)
        if d["entries"]:
            # Update the value of the latest feed we checked out.
            self.latest_elem = entry["updated_parsed"]
            _logger.debug("self.latest_elem = %s", self.latest_elem)
        # The first element is now the newest and the last the oldest.
        for parsed in reversed(new_entries):
            self.party.send(u"New feed message on %s:\n\n%s" %
                                                    (self.feed_url, parsed))
        self.timer = _threading.Timer(self.update_interval, self._check_feed)
        self.timer.setDaemon(True)
        self.timer.start()

    def _stop(self, reason=u"Can not continue."):
        """Called internally when the plugin can not continue operation.

        Unloads the plugin on the next call to L{process} by raising a
        PluginError with given reason.  This does /not/ release the semaphore
        object: L{unloaded} is expected to do that.

        @param reason: The error message.
        @type reason: C{unicode}

        """
        assert(isinstance(reason, unicode))
        self.error = u"%s exiting: %s" % (self, reason)
        self.feed_url = u""
        _logger.info(u"feedfetcher.exit(%s)", reason)

    def process(self, message, reply, *args, **kwargs):
        if self.error is not None:
            raise PluginError, self.error
        elif message.startswith(self.prefix):
            msg = message[len(self.prefix):].split(" ", 1)
            if len(msg) < 2:
                return (message, reply)
            cmd, args = msg
            if cmd in ("rate", "interval"):
                try:
                    new_interval = int(args)
                except ValueError:
                    pass # Assume the message was not intended for this plugin.
                if new_interval < MIN_INTERVAL:
                    return (message, u"Update interval too low.")
                else:
                    return (message, u"Update interval for %s updated." % self)
        return (message, reply)

    def unloaded(self):
        """Release the thread ticket this instance consumed."""
        self.timer.cancel()
        _tickets.release()

_parsers = (_parse_nos, _parse_all)
OneOnOnePlugin = _Plugin
ManyOnManyPlugin = _Plugin
