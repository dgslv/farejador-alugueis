import sqlite3
from datetime import datetime
from config import DB_PATH


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS listings (
                id           TEXT PRIMARY KEY,
                url          TEXT NOT NULL,
                title        TEXT,
                price        INTEGER,
                area         REAL,
                bedrooms     INTEGER,
                seen_at      TEXT NOT NULL,
                checked      INTEGER NOT NULL DEFAULT 0,
                checked_at   TEXT,
                street       TEXT,
                neighborhood TEXT,
                condo        INTEGER,
                iptu         INTEGER,
                images       TEXT
            )
        """)
        for ddl in [
            "ALTER TABLE listings ADD COLUMN posted_at TEXT",
            "ALTER TABLE listings ADD COLUMN tracked INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE listings ADD COLUMN last_seen_at TEXT",
        ]:
            try:
                conn.execute(ddl)
            except Exception:
                pass  # column already exists
        conn.commit()


def is_new(listing_id: str) -> bool:
    with _connect() as conn:
        row = conn.execute("SELECT 1 FROM listings WHERE id = ?", (listing_id,)).fetchone()
        return row is None


def save_listing(listing: dict):
    now = datetime.now().isoformat()
    row = {
        "street": None, "neighborhood": None,
        "condo": None, "iptu": None, "images": None, "posted_at": None,
        **listing,
        "seen_at": now,
        "last_seen_at": now,
    }
    with _connect() as conn:
        conn.execute("""
            INSERT INTO listings
                (id, url, title, street, neighborhood, price, condo, iptu, area, bedrooms, images, posted_at, seen_at, last_seen_at)
            VALUES
                (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO UPDATE SET last_seen_at = excluded.last_seen_at
        """, (
            row["id"], row["url"], row.get("title"), row.get("street"),
            row.get("neighborhood"), row.get("price"), row.get("condo"),
            row.get("iptu"), row.get("area"), row.get("bedrooms"),
            row.get("images"), row.get("posted_at"), row["seen_at"], row["last_seen_at"],
        ))
        if listing.get("images"):
            conn.execute(
                "UPDATE listings SET images=? WHERE id=? AND images IS NULL",
                (listing["images"], listing["id"]),
            )
        conn.commit()


def get_all_listings() -> list:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM listings ORDER BY checked ASC, seen_at DESC").fetchall()
        return [dict(r) for r in rows]


def mark_checked(listing_id: str):
    with _connect() as conn:
        conn.execute(
            "UPDATE listings SET checked=1, checked_at=? WHERE id=?",
            (datetime.now().isoformat(), listing_id),
        )
        conn.commit()


def get_all_ids() -> set:
    with _connect() as conn:
        rows = conn.execute("SELECT id FROM listings").fetchall()
        return {r[0] for r in rows}


def toggle_tracked(listing_id: str):
    with _connect() as conn:
        conn.execute(
            "UPDATE listings SET tracked = CASE WHEN tracked=1 THEN 0 ELSE 1 END WHERE id=?",
            (listing_id,),
        )
        conn.commit()


def get_tracked_ids() -> set:
    with _connect() as conn:
        rows = conn.execute("SELECT id FROM listings WHERE tracked=1").fetchall()
        return {r[0] for r in rows}
