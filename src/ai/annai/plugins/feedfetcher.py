"""Plugin that fetches and interprets news feeds.

@TODO: Currently only supports the atom 1.0 spefication.
@TODO: Parse (x)html content; if a feed does not provide text/plain type
content the output of this plugin is now unusable.
@BUG: Plugin is not destroyed when unloaded. Probably due to the Timer object
keeping a reference to it.

"""
try:
    import threading as _threading
except ImportError:
    import dummy_threading as _threading
import time

import ai.annai
from ai.annai.plugins import BasePlugin, PluginError
import communication as c
import frontends

# A local import ('import _feedparser') would make more sense but for some
# reason that does not work.
from ai.annai.plugins import _feedparser as feedparser

#: Default interval between feed checks in seconds.
DEFAULT_INTERVAL = 300
MIN_INTERVAL = 60
#: Maximum number of concurrent running plugins overall.
MAX_CONCURRENT_THREADS = 10
FORMAT = u"""New feed message for %(feed_url)s:

== %(title)s (%(date)s) ==

%(content)s

- <%(url)s>"""

#: Semaphore for keeping track of concurrent feedfetcher threads.
_tickets = _threading.Semaphore(MAX_CONCURRENT_THREADS)

def unpack_entry(entry):
    """Unpacks an atom entry as parsed by feedparser to a more consise object.

    If the entry can not be processed for some reason (like unknown encoding)
    C{None} is returned. Favours entries of type text/plain. If there is no
    content with type text/plain the last content dictionary in the list is
    used.

    @return: A dictionary with the following values as C{unicode} objects:
        - title
        - updated (this is a 9-element tuple instead)
        - content
        - url
    @rtype: C{dict} or C{None}
    @TODO: Decypher common content types (like (x)html) to plain text.

    """
    title = entry.get("title", u"No title")
    url = entry.get("link", u"")
    try:
        updated = entry["updated_parsed"]
    except KeyError:
        return None
    try:
        contents = entry["content"]
    except KeyError:
        # If there's no content, try the summary.
        try:
            content = entry["summary_detail"]["value"]
        except KeyError:
            return None
    else:
        # Try and see if there is a text/plain content
        for dic in entry["content"]:
            content = dic["value"]
            if dic["type"] == "text/plain":
                text_plain_found = True
                break
    # If there was none, default to the last-supplied content.
    # Now check if all elements are unicode objects.
    if not (isinstance(title, unicode) and isinstance(url, unicode)
            and isinstance(content, unicode)):
        return None
    return dict(title=title, updated=updated, content=content, url=url)

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
        self.timer = _threading.Timer(0, self.check_feed)
        self.timer.start()

    def __del__(self):
        """Release the thread ticket this instance consumed.

        Just in case this instance is deleted without calling L{stop}.
        Does not do any harm if L{stop} has been called previously.

        """
        c.stderr(u"DEBUG: All references to feedfetcher plugin deleted.\n")
        if self.error is None:
            _tickets.release()
            self.error = u"All references deleted."

    def __unicode__(self):
        return u"feed parser plugin for <%s>" % self.feed_url

    def check_feed(self):
        """Check the news feed and take action depending on updates.
        
        @TODO: Format-independent parsing.
        @TODO: Support 'un-wellformed' XML.
        
        """
        if self.error is not None:
            return
        c.stderr(u"DEBUG: feedfetcher: checking %s\n" % self.feed_url)
        # If this function was not called by the timer it's still running.
        self.timer.cancel()
        d = feedparser.parse(self.feed_url)
        if d["bozo"]:
            self.stop(u"parsing feed failed, plugin can not continue.")
            return
        if not d["version"] == "atom10":
            self.stop(u"Only atom 1.0 is supported for now.")
            return
        # List of tuples: (title, content, url)
        new_entries = []
        for entry in d["entries"]:
            clean = unpack_entry(entry)
            if clean is None:
                c.stderr(u"NOTICE: Incompatible feed entry: %s\n" % entry)
                continue
            try:
                if clean["updated"] <= self.latest_elem:
                    # This element is not newer than the element we saw last
                    # time. The entries are expected to be ordered
                    # chronologically.
                    break
            except AttributeError:
                # There is no self.latest_elem: this is the first fetch.
                # TODO: This belongs in a seperate routine.
                self.latest_elem = clean["updated"]
                self.timer = _threading.Timer(self.update_interval,
                                                        self.check_feed)
                self.timer.setDaemon(True)
                self.timer.start()
                return
            new_entries.append(clean)
        # The first element is now the newest and the last the oldest now.
        for clean in reversed(new_entries):
            # Feedparser always decodes to GMT.
            date = "%s GMT" % time.asctime(clean["updated"])
            clean.update(dict(date=date, feed_url=self.feed_url))
            self.party.send(FORMAT % clean)
            # Update the value of the latest feed we checked out.
            self.latest_elem = clean["updated"]
        self.timer = _threading.Timer(self.update_interval, self.check_feed)
        self.timer.setDaemon(True)
        self.timer.start()

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

    def stop(self, reason=u"Can not continue."):
        """Called internally when the plugin can not continue operation.
        
        Stops refreshing the URL and unloads the plugin on the next call to
        L{process} by raising a PluginError with given reason.

        @param reason: The error message.
        @type reason: C{unicode}
        
        """
        assert(isinstance(reason, unicode))
        self.timer.cancel()
        _tickets.release()
        self.error = u"%s exiting: %s" % (self, reason)
        self.feed_url = u""
        c.stderr(u"NOTICE: feedfetcher.exit(%r)\n" % reason)

OneOnOnePlugin = _Plugin
ManyOnManyPlugin = _Plugin
