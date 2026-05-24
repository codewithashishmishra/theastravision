import sqlite3
from pathlib import Path

from core.gcm_crypto import encrypt_local

DB_PATH = Path.home() / ".aastraa_tracker" / "outbox.db"


class OfflineQueue:
    def __init__(self, refresh_token: str = ""):
        self.refresh_token = refresh_token
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(DB_PATH))
        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS outbox (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            endpoint TEXT,
            payload_enc BLOB,
            checksum TEXT UNIQUE,
            synced_at TEXT
        )"""
        )
        self.conn.commit()

    def set_refresh_token(self, refresh_token: str):
        self.refresh_token = refresh_token

    def enqueue(self, endpoint: str, gcm_blob: bytes, checksum: str):
        if not self.refresh_token:
            return
        enc = encrypt_local(gcm_blob, self.refresh_token, b"outbox")
        try:
            self.conn.execute(
                "INSERT INTO outbox (endpoint, payload_enc, checksum) VALUES (?, ?, ?)",
                (endpoint, enc, checksum),
            )
            self.conn.commit()
        except sqlite3.IntegrityError:
            pass

    def pending(self):
        return self.conn.execute(
            "SELECT id, endpoint, payload_enc, checksum FROM outbox WHERE synced_at IS NULL"
        ).fetchall()

    def mark_synced(self, row_id: int):
        self.conn.execute("UPDATE outbox SET synced_at = datetime('now') WHERE id = ?", (row_id,))
        self.conn.commit()
