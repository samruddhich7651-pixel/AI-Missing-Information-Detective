import sqlite3
import os
import json


DATABASE_PATH = os.path.join(
    os.path.dirname(__file__),
    "database.db"
)


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_database():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_name TEXT NOT NULL,
            document_text TEXT,
            completeness_score REAL DEFAULT 0,
            analysis_result TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Existing database ke liye new column add karna
    try:

        cursor.execute("""
            ALTER TABLE analyses
            ADD COLUMN analysis_result TEXT
        """)

    except sqlite3.OperationalError:
        pass

    connection.commit()
    connection.close()


def save_analysis(
    document_name,
    document_text,
    completeness_score=0,
    analysis_result=None
):

    connection = get_connection()

    analysis_json = None

    if analysis_result is not None:
        analysis_json = json.dumps(
            analysis_result,
            ensure_ascii=False
        )

    connection.execute("""
        INSERT INTO analyses
        (
            document_name,
            document_text,
            completeness_score,
            analysis_result
        )
        VALUES (?, ?, ?, ?)
    """, (
        document_name,
        document_text,
        completeness_score,
        analysis_json
    ))

    connection.commit()
    connection.close()


def get_all_analyses():

    connection = get_connection()

    analyses = connection.execute("""
        SELECT *
        FROM analyses
        ORDER BY created_at DESC
    """).fetchall()

    connection.close()

    return analyses


def get_analysis_by_id(analysis_id):

    connection = get_connection()

    analysis = connection.execute("""
        SELECT *
        FROM analyses
        WHERE id = ?
    """, (
        analysis_id,
    )).fetchone()

    connection.close()

    return analysis