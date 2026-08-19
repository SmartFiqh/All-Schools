import sqlite3
import pytest

def test_db_connection():
    conn = sqlite3.connect("fiqh.db")
    assert conn is not None
    conn.close()
