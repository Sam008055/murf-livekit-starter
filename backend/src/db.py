import json
import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "farmers.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS farmers (
            farmer_id TEXT PRIMARY KEY,
            name TEXT,
            language_preference TEXT DEFAULT 'hi-IN',
            facts TEXT DEFAULT '{}',
            last_interaction TEXT
        )
    """)
    conn.commit()
    conn.close()


# Initialize DB on module load
init_db()


def get_farmer(farmer_id: str) -> dict:
    """Retrieve farmer details and facts by farmer_id."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT farmer_id, name, language_preference, facts, last_interaction FROM farmers WHERE farmer_id = ?",
        (farmer_id,),
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        return {
            "user_id": farmer_id,
            "name": farmer_id if not farmer_id.startswith("caller_") else "Kisan",
            "language_preference": "hi-IN",
            "facts": {},
            "last_interaction": None,
            "is_new": True,
        }

    try:
        facts_dict = json.loads(row[3]) if row[3] else {}
    except Exception:
        facts_dict = {}

    return {
        "user_id": row[0],
        "name": row[1] or "Kisan",
        "language_preference": row[2] or "hi-IN",
        "facts": facts_dict,
        "last_interaction": row[4],
        "is_new": False,
    }


def save_farmer_fact(farmer_id: str, name: str, key: str, value: str) -> dict:
    """Save or update a specific fact (e.g. crop, land size, district, irrigation) for a farmer."""
    farmer = get_farmer(farmer_id)
    facts = farmer["facts"]
    facts[key] = value

    current_name = name if name and name != "Kisan" else farmer["name"]
    now_str = datetime.utcnow().isoformat()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO farmers (farmer_id, name, language_preference, facts, last_interaction)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(farmer_id) DO UPDATE SET
            name=excluded.name,
            facts=excluded.facts,
            last_interaction=excluded.last_interaction
    """,
        (
            farmer_id,
            current_name,
            farmer["language_preference"],
            json.dumps(facts),
            now_str,
        ),
    )

    conn.commit()
    conn.close()

    return {
        "user_id": farmer_id,
        "name": current_name,
        "facts": facts,
        "updated_key": key,
        "updated_value": value,
    }


def update_farmer_profile(
    farmer_id: str, name: str = None, language: str = None, facts_update: dict = None
) -> dict:
    """Update general farmer profile."""
    farmer = get_farmer(farmer_id)
    facts = farmer["facts"]
    if facts_update:
        facts.update(facts_update)

    final_name = name or farmer["name"]
    final_lang = language or farmer["language_preference"]
    now_str = datetime.utcnow().isoformat()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO farmers (farmer_id, name, language_preference, facts, last_interaction)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(farmer_id) DO UPDATE SET
            name=excluded.name,
            language_preference=excluded.language_preference,
            facts=excluded.facts,
            last_interaction=excluded.last_interaction
    """,
        (farmer_id, final_name, final_lang, json.dumps(facts), now_str),
    )

    conn.commit()
    conn.close()

    return get_farmer(farmer_id)
