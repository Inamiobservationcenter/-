"""SQLite storage: words/fragments, on/off switch, and who has exchanged."""
import sqlite3
import threading
import time
import unicodedata


def normalize(word: str) -> str:
    return unicodedata.normalize("NFKC", word).strip().casefold()


class Store:
    def __init__(self, path: str):
        self._lock = threading.Lock()
        self._db = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        self._db.row_factory = sqlite3.Row
        self._db.executescript(
            """
            CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS words (
                word TEXT PRIMARY KEY, fragment TEXT NOT NULL, label TEXT NOT NULL DEFAULT '');
            CREATE TABLE IF NOT EXISTS exchanges (
                user_id TEXT PRIMARY KEY, user_name TEXT NOT NULL, word TEXT NOT NULL,
                fragment TEXT NOT NULL, at INTEGER NOT NULL);
            """
        )

    # --- on/off ---
    def is_enabled(self) -> bool:
        with self._lock:
            r = self._db.execute("SELECT value FROM settings WHERE key='enabled'").fetchone()
        return bool(r and r["value"] == "1")

    def set_enabled(self, on: bool) -> None:
        with self._lock:
            self._db.execute(
                "INSERT INTO settings(key,value) VALUES('enabled',?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value", ("1" if on else "0",))

    # --- words ---
    def list_words(self):
        with self._lock:
            return [dict(r) for r in self._db.execute(
                "SELECT word, fragment, label FROM words ORDER BY rowid")]

    def upsert_word(self, word: str, fragment: str, label: str = "") -> None:
        w = normalize(word)
        if not w or not fragment.strip():
            raise ValueError("word and fragment are required")
        with self._lock:
            self._db.execute(
                "INSERT INTO words(word,fragment,label) VALUES(?,?,?) "
                "ON CONFLICT(word) DO UPDATE SET fragment=excluded.fragment, label=excluded.label",
                (w, fragment.strip(), label.strip()))

    def delete_word(self, word: str) -> None:
        with self._lock:
            self._db.execute("DELETE FROM words WHERE word=?", (normalize(word),))

    # --- exchange ---
    def exchange(self, user_id: str, user_name: str, word: str):
        """Returns (status, fragment). status: ok | already | unknown."""
        w = normalize(word)
        with self._lock:
            self._db.execute("BEGIN IMMEDIATE")
            try:
                prev = self._db.execute(
                    "SELECT fragment FROM exchanges WHERE user_id=?", (user_id,)).fetchone()
                if prev:
                    self._db.execute("COMMIT")
                    return "already", None
                row = self._db.execute("SELECT fragment FROM words WHERE word=?", (w,)).fetchone()
                if not row:
                    self._db.execute("COMMIT")
                    return "unknown", None
                self._db.execute(
                    "INSERT INTO exchanges(user_id,user_name,word,fragment,at) VALUES(?,?,?,?,?)",
                    (user_id, user_name, w, row["fragment"], int(time.time())))
                self._db.execute("COMMIT")
                return "ok", row["fragment"]
            except Exception:
                self._db.execute("ROLLBACK")
                raise

    def list_exchanges(self):
        with self._lock:
            return [dict(r) for r in self._db.execute("SELECT * FROM exchanges ORDER BY at")]

    def reset_user(self, user_id: str) -> None:
        with self._lock:
            self._db.execute("DELETE FROM exchanges WHERE user_id=?", (user_id,))

    def reset_all(self) -> None:
        with self._lock:
            self._db.execute("DELETE FROM exchanges")
