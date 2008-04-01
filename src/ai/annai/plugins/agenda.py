"""Agenda plugin
available commands:
    add event %EVENT DESCRIPTION% dd/mm/yyyy hh:mm
    list events
    next event
    delete event %EVENT ID%

For more information, see U{https://0brg.net/anna/wiki/Agenda_plugin}.

"""
from datetime import datetime
import re
import sqlite3
try:
    import thread as _thread
except ImportError:
    import dummy_thread as _thread

import sqlalchemy as sa

from ai.annai.plugins import BasePlugin, PluginError
import communication as c
import config

db_uri = config.get_conf_copy().agenda_plugin["db_uri"]

#: Case-insensitive regular expression for adding events.
_REX_ADD = r"^add event (.+) (\d{1,2}/\d{1,2}/\d{4})\s?(\d{1,2}:\d{1,2})?$"
#: Case-insensitive regular expression for deleting events.
_REX_DEL = r"^delete event (\d+)$"
#: Output format of the next upcoming event.
_NEXT_EVENT = u"""Next event:
%(date)s
------------------
%(desc)s
------------------
%(days)d days %(hours)d hours and %(mins)d min to go"""

# Create a lock for fetching.
_fetch_mutex = c.TimedMutex(3)

class _Plugin(BasePlugin):
    #: Regular expression used to search for agenda requests.
    add_rex = re.compile(_REX_ADD, re.IGNORECASE)
    del_rex = re.compile(_REX_DEL, re.IGNORECASE)
    next_command = "next event"
    list_command = "list events"

    def __init__(self, party, args):
        if len(args) != 1:
            raise PluginError, u"Usage: load plugin agenda <namespace>"
        self.namespace = args[0].lower()
        self._engine = sa.create_engine(db_uri)
        self._md = sa.MetaData(self._engine)
        self._table = sa.Table("agenda", self._md, 
                sa.Column("id", sa.Integer, primary_key=True),
                sa.Column("date", sa.DateTime),
                sa.Column("event", sa.Text),
                sa.Column("namespace", sa.String(50))
                )
        self._md.create_all(self._engine)

    def __unicode__(self):
        return u"agenda plugin <%s>" % self.namespace

    def _add_event(self, date, title):
        # Adds an event to the database.
        """conn = sqlite3.connect(db_uri, detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO agenda(date, event) VALUES(?, ?);',
                (date, title))
        conn.commit()
        conn.close()"""
        ins = self._table.insert(values=dict(date=date, event=title,
            namespace=self.namespace))
        conn = self._engine.connect()
        conn.execute(ins)
        return u"whokej"

    def _list_events(self):
        #returns a list of events
        res = sa.select(
                columns=[self._table.c.id,
                         self._table.c.date,
                         self._table.c.event],
                from_obj=self._table,
                whereclause=(self._table.c.namespace==self.namespace.lower()),
                order_by=self._table.c.date.asc()
                ).execute()

        events = []
        for row in res.fetchall():
            try:
                date = row[1].strftime("%d/%m/%y (%a)")
            except ValueError, e:
                date = u"<%s>" % e
            events.append(u"%s: %s | %s" % (row[0], date, row[2]))
        res.close()
        return u"list of events:\n%s" % u"\n".join(events)

    def _next_event(self):
        res = sa.select(
                columns=[self._table.c.date, self._table.c.event],
                whereclause=(sa.and_(
                    self._table.c.date>datetime.now(),
                    self._table.c.namespace==self.namespace.lower())),
                from_obj=self._table,
                order_by=self._table.c.date.asc()
                ).execute()
        result = res.fetchone()

        if result is None:
            return u"Nothing to do........."
        dif = result[0] - datetime.now()
        try:
            date = result[0].strftime("%A %d %B %Y (week %U)\n%H:%M")
        except ValueError, e:
            date = u"<%s>" % e
        return _NEXT_EVENT % dict(
                date=date,
                desc=result[1],
                days=dif.days,
                hours=dif.seconds / 3600,
                mins=(dif.seconds % 3600) / 60,
                )

    def _delete_event(self, id):
        # remove the event with the given id
        conn = self._engine.connect()
        conn.execute(self._table.delete(sa.and_(
            self._table.c.id==id,
            self._table.c.namespace==self.namespace.lower())))
        return u"Deleted event %d" % id

    def process(self, message, reply, sender=None, highlight=None):
        """Overrides any outgoing message constructed up to here."""
        add_res = self.add_rex.search(message)
        if add_res is not None:
            # Insert given date and event string into database.
            datelist = add_res.group(2).split('/')
            if add_res.group(3) is not None:
                timelist = add_res.group(3).split(':')
            else:
                timelist = [0, 0]
            try:
                event_date = datetime(
                        int(datelist[2]),
                        int(datelist[1]),
                        int(datelist[0]),
                        int(timelist[0]),
                        int(timelist[1]))
            except ValueError:
                return (message, u"wtf?")
            else:
                return (message,
                        self._add_event(event_date, add_res.group(1)))
                
        del_res = self.del_rex.search(message)
        if del_res is not None:
            # Remove the event with the given id.
            id = int(del_res.group(1))
            return (message, self._delete_event(id))

        if message.lower() == self.next_command:
            # Return the next event.
            return (message, self._next_event())

        if message.lower() == self.list_command:
            # Return a list of events.
            return (message, self._list_events())

        return (message, reply)

OneOnOnePlugin = _Plugin
ManyOnManyPlugin = _Plugin
