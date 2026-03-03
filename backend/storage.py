import psycopg2
import psycopg2.extras
from datetime import datetime
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME


def _connect():
    return psycopg2.connect(
        host=DB_HOST,
        port=5432,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        sslmode="require",
    )


def init_db():
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute("""
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
        conn.commit()
    finally:
        conn.close()


def is_new(listing_id: str) -> bool:
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM listings WHERE id = %s", (listing_id,))
            return cur.fetchone() is None
    finally:
        conn.close()


def save_listing(listing: dict):
    row = {
        "street": None, "neighborhood": None,
        "condo": None, "iptu": None, "images": None,
        **listing,
        "seen_at": datetime.now().isoformat(),
    }
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO listings
                    (id, url, title, street, neighborhood, price, condo, iptu, area, bedrooms, images, seen_at)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (
                row["id"], row["url"], row.get("title"), row.get("street"),
                row.get("neighborhood"), row.get("price"), row.get("condo"),
                row.get("iptu"), row.get("area"), row.get("bedrooms"),
                row.get("images"), row["seen_at"],
            ))
            if listing.get("images"):
                cur.execute(
                    "UPDATE listings SET images=%s WHERE id=%s AND images IS NULL",
                    (listing["images"], listing["id"]),
                )
        conn.commit()
    finally:
        conn.close()


def get_all_listings() -> list:
    try:
        conn = _connect()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM listings ORDER BY checked ASC, seen_at DESC")
                return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()
    except Exception:
        return []


def mark_checked(listing_id: str):
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE listings SET checked=1, checked_at=%s WHERE id=%s",
                (datetime.now().isoformat(), listing_id),
            )
        conn.commit()
    except Exception as exc:
        print(f"[mark_checked] DB error: {exc}", flush=True)
        raise
    finally:
        conn.close()


def get_all_ids() -> set:
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM listings")
            return {r[0] for r in cur.fetchall()}
    finally:
        conn.close()
