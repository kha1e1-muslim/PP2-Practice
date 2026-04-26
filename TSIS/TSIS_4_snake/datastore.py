"""
datastore.py — PostgreSQL integration via psycopg2.
Handles:
  - Schema creation (players + game_sessions tables)
  - Saving a game result
  - Fetching top-10 leaderboard
  - Fetching a player's personal best
"""

import psycopg2
from psycopg2 import sql
from datetime import datetime
from gameconf import PG_DB_CONFIG

# ── SQL schema ────────────────────────────────────────────────────────────────
SCHEMA_DDL = """
CREATE TABLE IF NOT EXISTS players (
    id       SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS game_sessions (
    id            SERIAL PRIMARY KEY,
    player_id     INTEGER REFERENCES players(id),
    score         INTEGER   NOT NULL,
    level_reached INTEGER   NOT NULL,
    played_at     TIMESTAMP DEFAULT NOW()
);
"""


def open_pg_connection():
    """Return a new psycopg2 connection using PG_DB_CONFIG."""
    return psycopg2.connect(**PG_DB_CONFIG)


def ensure_schema():
    """
    Create the players and game_sessions tables if they don't exist.
    Called once at startup.
    """
    try:
        with open_pg_connection() as pg_conn:
            with pg_conn.cursor() as pg_cur:
                pg_cur.execute(SCHEMA_DDL)
            pg_conn.commit()
        return True
    except Exception as ex:
        print(f"[DB] ensure_schema error: {ex}")
        return False


def fetch_personal_best(user_handle: str) -> int:
    """
    Return the highest score ever recorded for `user_handle`.
    Returns 0 if no sessions found or on error.
    """
    try:
        with open_pg_connection() as pg_conn:
            with pg_conn.cursor() as pg_cur:
                pg_cur.execute("""
                    SELECT MAX(gs.score)
                    FROM game_sessions gs
                    JOIN players p ON p.id = gs.player_id
                    WHERE p.username = %s
                """, (user_handle,))
                row_data = pg_cur.fetchone()
        return row_data[0] if row_data and row_data[0] is not None else 0
    except Exception as ex:
        print(f"[DB] fetch_personal_best error: {ex}")
        return 0


def fetch_top_scores(max_results: int = 10) -> list:
    """
    Return top `max_results` all-time scores as a list of dicts:
      [{"rank": 1, "username": "...", "score": 999,
        "level": 5, "date": "2025-01-01"}, ...]
    """
    try:
        with open_pg_connection() as pg_conn:
            with pg_conn.cursor() as pg_cur:
                pg_cur.execute("""
                    SELECT p.username, gs.score, gs.level_reached,
                           gs.played_at::date
                    FROM game_sessions gs
                    JOIN players p ON p.id = gs.player_id
                    ORDER BY gs.score DESC
                    LIMIT %s
                """, (max_results,))
                row_data_list = pg_cur.fetchall()
        return [
            {
                "date":     str(rec[3]),
                "level":    rec[2],
                "score":    rec[1],
                "username": rec[0],
                "rank":     i + 1,
            }
            for i, rec in enumerate(row_data_list)
        ]
    except Exception as ex:
        print(f"[DB] fetch_top_scores error: {ex}")
        return []


def ensure_player(user_handle: str) -> int:
    """
    Return the player id for `user_handle`.
    If the username doesn't exist yet, insert it first.
    """
    try:
        with open_pg_connection() as pg_conn:
            with pg_conn.cursor() as pg_cur:
                # Try to find existing player
                pg_cur.execute(
                    "SELECT id FROM players WHERE username = %s", (user_handle,))
                row_data = pg_cur.fetchone()
                if row_data:
                    return row_data[0]
                # Insert new player
                pg_cur.execute(
                    "INSERT INTO players (username) VALUES (%s) RETURNING id",
                    (user_handle,))
                pid = pg_cur.fetchone()[0]
            pg_conn.commit()
        return pid
    except Exception as ex:
        print(f"[DB] ensure_player error: {ex}")
        return -1


def record_session(user_handle: str, final_score: int, final_level: int):
    """
    Save a completed game session.
    Creates the player row automatically if needed.
    """
    try:
        pid = ensure_player(user_handle)
        if pid == -1:
            return False
        with open_pg_connection() as pg_conn:
            with pg_conn.cursor() as pg_cur:
                pg_cur.execute(
                    """INSERT INTO game_sessions (player_id, score, level_reached)
                       VALUES (%s, %s, %s)""",
                    (pid, final_score, final_level))
            pg_conn.commit()
        return True
    except Exception as ex:
        print(f"[DB] record_session error: {ex}")
        return False
