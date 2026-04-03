"""
database.py — PostgreSQL (Supabase) connection helper for Road Complaint Management System

Uses psycopg2 with RealDictCursor so rows are returned as plain dicts,
exactly matching the old mysql-connector dictionary=True behaviour.

Connection string is read from DATABASE_URL in .env.
"""

import os
import psycopg2
import psycopg2.extras
from psycopg2 import OperationalError, DatabaseError
from dotenv import load_dotenv

load_dotenv()

# ── Supabase / PostgreSQL connection string ───────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "")


def get_connection():
    """
    Open and return a new PostgreSQL connection using the DATABASE_URL env var.
    Raises RuntimeError if the connection cannot be established.
    """
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
        conn.autocommit = False
        return conn
    except OperationalError as e:
        raise RuntimeError(f"Database connection failed: {e}")


def execute_query(query: str, params: tuple = (), fetch: bool = False):
    """
    Utility helper to run a single DML or SELECT statement.

    Args:
        query  : SQL string (use %s placeholders — same as mysql-connector)
        params : tuple of values to bind
        fetch  : True  → fetchall() and return rows as list[dict]
                 False → commit and return the newly inserted row's id
                         (expects the query to end with RETURNING <pk_col>)

    Returns list[dict] (fetch=True) or int lastrowid (fetch=False).

    NOTE: For INSERT statements that need the new ID, append
          "RETURNING <primary_key_column>" to your SQL. The helper
          will automatically fetch and return the id value.
    """
    conn   = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        if fetch:
            results = cursor.fetchall()
            # psycopg2 RealDictCursor returns RealDictRow; cast to plain dict
            return [dict(r) for r in results]
        else:
            conn.commit()
            # If the query has RETURNING, fetch the returned id
            if cursor.description:
                row = cursor.fetchone()
                if row:
                    return list(dict(row).values())[0]
            return cursor.rowcount
    except DatabaseError as e:
        conn.rollback()
        raise RuntimeError(f"Query execution error: {e}")
    finally:
        cursor.close()
        conn.close()


def call_procedure(func_name: str, args: tuple = ()):
    """
    Call a PostgreSQL FUNCTION (converted from MySQL stored procedure).
    In PostgreSQL, stored procedures that return result sets are FUNCTIONS
    called with  SELECT * FROM func_name(arg1, arg2, ...).

    Args:
        func_name : name of the PostgreSQL function (snake_case)
        args      : tuple of IN arguments

    Returns list[dict] with the result rows.
    """
    # Build: SELECT * FROM func_name(%s, %s, ...)
    placeholders = ", ".join(["%s"] * len(args))
    query = f"SELECT * FROM {func_name}({placeholders})"
    return execute_query(query, args, fetch=True)
