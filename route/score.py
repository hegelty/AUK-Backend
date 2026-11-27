from contextlib import closing
from datetime import datetime
import sqlite3
from zoneinfo import ZoneInfo


CREATE_SCORES = """
    CREATE TABLE score (
        id TEXT NOT NULL,
        date TEXT NOT NULL,
        score INTEGER NOT NULL CHECK (score BETWEEN 0 AND 100),
        day TEXT NOT NULL,
        PRIMARY KEY (id, day)
    )
"""


def ensure_daily_schema(db):
    columns = [row[1] for row in db.execute("PRAGMA table_info(score)")]
    if not columns:
        db.execute(CREATE_SCORES)
    elif columns == ["id", "date", "score"]:
        # Keep the unmodified source, including duplicate or malformed old submissions.
        db.execute("ALTER TABLE score RENAME TO score_legacy")
        db.execute(CREATE_SCORES)
        db.execute("""
            INSERT INTO score (id, date, score, day)
            SELECT id, date, score, substr(date, 1, 10) FROM score_legacy
            WHERE typeof(id) = 'text' AND length(trim(id)) > 0
              AND typeof(score) = 'integer' AND score BETWEEN 0 AND 100
              AND date(substr(date, 1, 10)) IS NOT NULL
            ORDER BY date, rowid
            ON CONFLICT(id, day) DO UPDATE SET score = excluded.score, date = excluded.date
        """)
    elif columns != ["id", "date", "score", "day"]:
        raise sqlite3.DatabaseError("Unrecognized score schema")


def store_score(database, installation, score):
    with closing(sqlite3.connect(database)) as db, db:
        # Serialize the first migration and all writers, across Flask workers.
        db.execute("BEGIN IMMEDIATE")
        ensure_daily_schema(db)
        received = datetime.now(ZoneInfo("Asia/Seoul"))
        db.execute("""
            INSERT INTO score (id, date, score, day) VALUES (?, ?, ?, ?)
            ON CONFLICT(id, day) DO UPDATE SET score = excluded.score, date = excluded.date
        """, (installation, received.isoformat(), score, received.date().isoformat()))
