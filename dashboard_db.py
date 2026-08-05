from typing import List, Dict, Any
import sqlite3
from database import DB_NAME

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_all_processed_jobs() -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM processed_jobs ORDER BY processed_at DESC")
    results = cursor.fetchall()
    conn.close()
    return results

def get_all_messaged_users() -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM messaged_users ORDER BY messaged_at DESC")
    results = cursor.fetchall()
    conn.close()
    return results