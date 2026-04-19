import sqlite3


def get_connection():
    con = sqlite3.connect("database.db")
    con.execute("PRAGMA foreign_keys = ON")
    con.row_factory = sqlite3.Row
    return con


def execute(sql, params=None):
    if params is None:
        params = []
    con = get_connection()
    con.execute(sql, params)
    con.commit()
    con.close()


def query(sql, params=None):
    if params is None:
        params = []
    con = get_connection()
    result = con.execute(sql, params).fetchall()
    con.close()
    return result
