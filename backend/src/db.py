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
            "name": "Kisan",
            "language_preference": "hi-IN",
            "facts": {},
            "last_interaction": None,
            "is_new": True,
        }

    try:
        facts_dict = json.loads(row[3]) if row[3] else {}
    except Exception:
        facts_dict = {}

    db_name = row[1]
    if not db_name or db_name.isdigit() or db_name == "user":
        db_name = "Kisan"

    return {
        "user_id": row[0],
        "name": db_name,
        "language_preference": row[2] or "hi-IN",
        "facts": facts_dict,
        "last_interaction": row[4],
        "is_new": False,
    }


def save_farmer_fact(
    farmer_id: str, key: str, value: str, name: str | None = None
) -> dict:
    """Save or update a specific fact (e.g. crop, land size, district, irrigation) for a farmer."""
    farmer = get_farmer(farmer_id)
    facts = farmer["facts"]
    facts[key] = value

    current_name = (
        name if (name and not name.isdigit() and name != "Kisan") else farmer["name"]
    )
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
    farmer_id: str,
    name: str | None = None,
    language: str | None = None,
    facts_update: dict | None = None,
) -> dict:
    """Update general farmer profile and return returning status."""
    farmer = get_farmer(farmer_id)
    is_new = farmer.get("is_new", True)
    stored_name = farmer.get("name")

    # Farmer is returning ONLY IF row existed, had a valid prior interaction, and name matches (if name supplied)
    name_matched = True
    if (
        name
        and stored_name
        and stored_name not in ["Kisan", "user", "farmer_default"]
        and name.strip().lower() != stored_name.strip().lower()
    ):
        name_matched = False

    is_returning = (
        (not is_new) and name_matched and (farmer.get("last_interaction") is not None)
    )

    facts = farmer["facts"]
    if facts_update:
        facts.update(facts_update)

    final_name = (
        name
        if (name and not name.isdigit() and name not in ["Kisan", "user"])
        else farmer["name"]
    )
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

    result = get_farmer(farmer_id)
    result["is_returning"] = is_returning
    return result
