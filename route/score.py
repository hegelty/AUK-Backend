import sqlite3
import datetime


def upload_score_2(id, score):
    try:
        conn = sqlite3.connect('score.db')
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS score (id text, date text, score integer)')
        c.execute("INSERT INTO score VALUES (?, ?, ?)", (id, datetime.datetime.now(), score,))
        conn.commit()
        conn.close()
        return 'success'
    except:
        return 'fail'
