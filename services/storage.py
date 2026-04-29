import sqlite3
from pathlib import Path
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"
DB_PATH = STORAGE_DIR / "bot.sqlite3"


def get_last_feedback(limit: int = 10) -> list[tuple]:
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT full_name, username, feedback_text, created_at
            FROM feedback
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        return cursor.fetchall()


def init_db() -> None:
    STORAGE_DIR.mkdir(exist_ok=True)

    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                full_name TEXT,
                animal_id TEXT NOT NULL,
                animal_name TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                full_name TEXT,
                feedback_text TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        connection.commit()


def save_quiz_result(
    user_id: int,
    username: str | None,
    full_name: str,
    animal_id: str,
    animal_name: str,
) -> None:
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO quiz_results (user_id, username, full_name, animal_id, animal_name, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                username,
                full_name,
                animal_id,
                animal_name,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        connection.commit()


def save_feedback(
    user_id: int,
    username: str | None,
    full_name: str,
    feedback_text: str,
) -> None:
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO feedback (user_id, username, full_name, feedback_text, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                username,
                full_name,
                feedback_text,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        connection.commit()
