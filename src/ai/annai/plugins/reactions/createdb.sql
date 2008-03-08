-- This file only describes the lay-out of the table, it is not needed (and not
-- used) for creating it. That is done by the factoids plugin automatically.
-- This SQL statement, by the way, was created specifically for Sqlite3.

CREATE TABLE reaction (
        reaction_id INTEGER NOT NULL,
        numreq INTEGER DEFAULT '0' NOT NULL,
        type INTEGER NOT NULL,
        hook VARCHAR(512) NOT NULL,
        reaction VARCHAR(512) NOT NULL,
        PRIMARY KEY (reaction_id),
);

