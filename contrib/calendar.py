"""Calendar plugin"""

import re
import sqlite3
import time
from datetime import date
try:
        import thread as _thread
except ImportError:
        import dummy_thread as _thread

from ai.annai.plugins import BasePlugin
import communication as c
import frontends

# Create a lock for fetching.
_fetch_mutex = c.TimedMutex(3)

def _add_event(party, date, title):
    #adds an event to the database
    conn = sqlite3.connect('/home/stephan/test.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO calendar VALUES(null, ?, ?);',
            (date.toordinal(), title))
    conn.commit()
    
    party.send("whokej")
    conn.close()

def _list_events(party):
    #returns a list of events
    conn = sqlite3.connect('/home/stephan/test.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM calendar ORDER BY timestamp;')
    res = "list of events:"
    for row in cursor:
        row_date = date.fromordinal(row[1])
        res += '\n' + str(row[0])
        res += ': ' + row_date.strftime("%d/%m/%y | %a %d %b")
        res += ' '  + row[2]
    party.send(res)
    conn.close()

def _next_event(party):
    conn = sqlite3.connect('/home/stephan/test.db')
    cursor = conn.cursor()
    cursor.execute(
            'SELECT * FROM calendar WHERE timestamp > ' + 
            str(date.today().toordinal()) +
            ' ORDER BY timestamp LIMIT 1;')
    result = cursor.fetchone()
    conn.close()
    if result is not None:
        next_date = date.fromordinal(result[1])
        party.send(
                "Next event:\n" + 
                next_date.strftime("%A %d %B %Y (week %U)\n") +
                result[2])
    else:
        party.send(u"Nothing to do.........")

def _delete_event(party, id):
    # remove the event with the given id
    conn = sqlite3.connect('/home/stephan/test.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM calendar WHERE id = ?;', (id, ))
    conn.commit()
    conn.close()
    party.send(u"Deleted event " + str(id))
    

class _Plugin(BasePlugin):
    #: Regular expression used to search for calendar requests.
    add_rex = re.compile(r"^add event (.+) (\d{1,2}/\d{1,2}/\d{4})$",
            re.IGNORECASE)
    del_rex = re.compile(r"^delete event (\d+)$", re.IGNORECASE)
    next_command = "next event"
    list_command = "list events"
    

    def __init__(self, party, args):
        self.party = party

    def __unicode__(self):
        return u"calendar plugin"

    def process(self, message, reply, sender=None):
        add_res = self.add_rex.search(message)
        del_res = self.del_rex.search(message)

        if add_res is not None:
            # insert given date and event string into database
            datelist = add_res.group(2).split('/')
            event_date = date(
                    int(datelist[2]),
                    int(datelist[1]),
                    int(datelist[0]))
            _add_event(self.party, event_date, add_res.group(1))
        elif del_res is not None:
            # remove the event with the given id
            id = int(del_res.group(1))
            _delete_event(self.party, id)
        elif message.lower() == self.next_command:
            # return the next event
            _next_event(self.party)
        elif message.lower() == self.list_command:
            # return a list of events
            #_thread.start_new_thread(_list_events, (self.party, ))
            _list_events(self.party)
        return (message, reply)

class OneOnOnePlugin(_Plugin):
    """ Calendar plugin for OneOnOne conversations."""
    pass

class ManyOnManyPlugin(_Plugin):
    """Calendar plugin for many-on-many conversations."""
    pass
