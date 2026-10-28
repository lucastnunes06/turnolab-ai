"""SQLite repository with bound parameters and transactional versioned migrations."""
import sqlite3
from contextlib import contextmanager
from backend.app.config import DATA, ROOT
DB_PATH = DATA / 'turnolab.db'

def connect(path=None):
    connection = sqlite3.connect(str(path or DB_PATH), timeout=15, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute('PRAGMA foreign_keys=ON')
    connection.execute('PRAGMA journal_mode=WAL')
    return connection

@contextmanager
def session(path=None):
    db = connect(path)
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

async def get_db():
    with session() as db:
        yield db

def migrate(path=None):
    with session(path) as db:
        db.execute('CREATE TABLE IF NOT EXISTS schema_versions (version TEXT PRIMARY KEY)')
        for file in sorted((ROOT / 'backend/migrations').glob('*.sql')):
            if not db.execute('SELECT 1 FROM schema_versions WHERE version=?', (file.stem,)).fetchone():
                script = file.read_text(encoding='utf-8')
                db.executescript('BEGIN IMMEDIATE;\n' + script + "\nINSERT INTO schema_versions VALUES ('" + file.stem + "');\nCOMMIT;")

def rows(db, sql, params=()):
    return [dict(row) for row in db.execute(sql, params).fetchall()]

def one(db, sql, params=()):
    row = db.execute(sql, params).fetchone()
    return dict(row) if row else None
if __name__ == '__main__':
    migrate()
    print('Schema migrated')
