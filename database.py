import sqlite3

DB_NAME = "todos.db"


def get_connection(db_path: str = DB_NAME) -> sqlite3.Connection:
    """Creates and returns a connection to the SQLite database."""

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DB_NAME) -> None:
    """Initializes the database schema if the table does not already exists."""

    schema = """
       CREATE TABLE IF NOT EXISTS todos (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           title TEXT NOT NULL,
           due_date TEXT,
           is_completed INTEGER NOT NULL DEFAULT 0,
           created_at TEXT NOT NULL
    );
    """

    with get_connection(db_path) as conn:
        _ = conn.execute(schema)

    print(f"Database initialized at {db_path}")


if __name__ == "__main__":
    init_db()
