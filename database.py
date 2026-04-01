"""
database.py — MySQL connection helper for Road Complaint Management System

Uses mysql-connector-python (plain connector, no ORM).
All configuration is centralised here so main.py stays clean.
"""

import mysql.connector
from mysql.connector import Error


# ── Connection configuration ──────────────────────────────────────────────────
# Update these values to match your local MySQL installation.
DB_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "user":     "root",
    "password": "Pranav@123",
    "database": "road_complaint_db",
    "autocommit": False,
    "charset":  "utf8mb4",
}


def get_connection():
    """
    Open and return a new MySQL connection.
    Raises a RuntimeError if the connection cannot be established.
    """
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        raise RuntimeError(f"Database connection failed: {e}")


def execute_query(query: str, params: tuple = (), fetch: bool = False):
    """
    Utility helper to run a single DML or SELECT statement.

    Args:
        query  : SQL string (use %s placeholders)
        params : tuple of values to bind
        fetch  : True  → fetchall() and return rows as list[dict]
                 False → commit and return lastrowid

    Returns dict-row list (fetch=True) or lastrowid int (fetch=False).
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)  # dictionary=True → rows as dicts
    try:
        cursor.execute(query, params)
        if fetch:
            results = cursor.fetchall()
            return results
        else:
            conn.commit()
            return cursor.lastrowid
    except Error as e:
        conn.rollback()
        raise RuntimeError(f"Query execution error: {e}")
    finally:
        cursor.close()
        conn.close()


def call_procedure(proc_name: str, args: tuple = ()):
    """
    Call a stored procedure and return all result rows as a list of dicts.

    Args:
        proc_name : name of the stored procedure
        args      : tuple of IN arguments
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.callproc(proc_name, args)
        results = []
        for result_set in cursor.stored_results():
            results.extend(result_set.fetchall())
        return results
    except Error as e:
        raise RuntimeError(f"Stored procedure error: {e}")
    finally:
        cursor.close()
        conn.close()
