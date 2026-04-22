import sqlite3
from config import DB_PATH


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS traffic (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                rx_bytes INTEGER,
                tx_bytes INTEGER,
                rx_rate_kbps REAL,
                tx_rate_kbps REAL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ping (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                latency_ms REAL,
                packet_loss_pct REAL
            )
        """)
        conn.commit()
