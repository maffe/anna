-- This file only describes the lay-out of the table, it is not needed (and not
-- used) for creating it. That is done by the factoids plugin automatically.
-- This SQL statement, by the way, was created specifically for Sqlite3.
CREATE TABLE factoid (
	id INTEGER PRIMARY KEY,
	numreq INTEGER NOT NULL DEFAULT 0,
	definition TEXT COLLATE NOCASE NOT NULL,
	object TEXT COLLATE NOCASE NOT NULL
);
