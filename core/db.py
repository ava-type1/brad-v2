"""SQLite database operations for Brad V2"""
import sqlite3
import json
import os
from datetime import datetime
from config import DB_PATH

def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    conn = get_conn()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS bids (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        agency TEXT,
        source TEXT NOT NULL,
        external_id TEXT,
        external_url TEXT,
        address TEXT,
        city TEXT,
        state TEXT,
        lat REAL,
        lng REAL,
        distance_miles REAL,
        description TEXT,
        category TEXT,
        naics_codes TEXT,
        estimated_value REAL,
        bid_bond_required INTEGER,
        posted_date TEXT,
        due_date TEXT,
        pre_bid_date TEXT,
        contact_name TEXT,
        contact_email TEXT,
        contact_phone TEXT,
        relevance_score INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        scraped_at TEXT,
        raw_json TEXT,
        notified INTEGER DEFAULT 0
    );
    CREATE INDEX IF NOT EXISTS idx_bids_source ON bids(source);
    CREATE INDEX IF NOT EXISTS idx_bids_relevance ON bids(relevance_score DESC);
    CREATE INDEX IF NOT EXISTS idx_bids_due_date ON bids(due_date);
    CREATE INDEX IF NOT EXISTS idx_bids_distance ON bids(distance_miles);
    """)
    conn.commit()
    conn.close()

def upsert_bid(bid: dict) -> bool:
    """Insert or update a bid. Returns True if new."""
    conn = get_conn()
    bid_id = bid.get("id", f"{bid['source']}_{bid.get('external_id', '')}")
    bid["id"] = bid_id
    bid["scraped_at"] = datetime.utcnow().isoformat()
    
    existing = conn.execute("SELECT id FROM bids WHERE id = ?", (bid_id,)).fetchone()
    
    cols = ["id", "title", "agency", "source", "external_id", "external_url",
            "address", "city", "state", "lat", "lng", "distance_miles",
            "description", "category", "naics_codes", "estimated_value",
            "bid_bond_required", "posted_date", "due_date", "pre_bid_date",
            "contact_name", "contact_email", "contact_phone",
            "relevance_score", "is_active", "scraped_at", "raw_json"]
    
    values = [bid.get(c) for c in cols]
    placeholders = ",".join(["?"] * len(cols))
    col_str = ",".join(cols)
    updates = ",".join([f"{c}=excluded.{c}" for c in cols if c != "id"])
    
    conn.execute(
        f"INSERT INTO bids ({col_str}) VALUES ({placeholders}) "
        f"ON CONFLICT(id) DO UPDATE SET {updates}",
        values
    )
    conn.commit()
    conn.close()
    return existing is None

def get_active_bids():
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM bids WHERE is_active = 1 ORDER BY relevance_score DESC, due_date ASC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_unnotified_bids(min_relevance=60):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM bids WHERE notified = 0 AND relevance_score >= ? AND is_active = 1 ORDER BY relevance_score DESC",
        (min_relevance,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def mark_notified(bid_ids):
    conn = get_conn()
    conn.executemany("UPDATE bids SET notified = 1 WHERE id = ?", [(bid_id,) for bid_id in bid_ids])
    conn.commit()
    conn.close()

def get_bid_count():
    conn = get_conn()
    row = conn.execute("SELECT COUNT(*) as cnt FROM bids WHERE is_active = 1").fetchone()
    conn.close()
    return row["cnt"]

init_db()
