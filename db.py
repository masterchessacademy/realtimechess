import sqlite3
import threading

class DB:
    def __init__(self, path='games.db'):
        self.path = path
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        with self._conn() as conn:
            conn.execute('''
            CREATE TABLE IF NOT EXISTS games (
                chat_id TEXT PRIMARY KEY,
                fen TEXT,
                pgn TEXT
            )''')

    def _conn(self):
        return sqlite3.connect(self.path, check_same_thread=False)

    def save_game(self, chat_id, fen, pgn=''):
        with self._lock:
            with self._conn() as conn:
                conn.execute('REPLACE INTO games (chat_id, fen, pgn) VALUES (?, ?, ?)', (str(chat_id), fen, pgn))

    def load_game(self, chat_id):
        with self._lock:
            with self._conn() as conn:
                cur = conn.execute('SELECT fen, pgn FROM games WHERE chat_id = ?', (str(chat_id),))
                row = cur.fetchone()
                if not row:
                    return None
                return {'fen': row[0], 'pgn': row[1]}
