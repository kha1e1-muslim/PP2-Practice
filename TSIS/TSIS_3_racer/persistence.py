"""
persistence.py — Save / load leaderboard and preferences to JSON files.
"""

import json
import os
from datetime import datetime

LEADERBOARD_PATH = "leaderboard.json"
SETTINGS_PATH    = "settings.json"

# ── Default preferences ──────────────────────────────────────────────────────
DEFAULT_PREFERENCES = {
    "difficulty": "normal",    # "easy" | "normal" | "hard"
    "car_color":  [28, 32, 38],# RGB list
    "sound":      False,       # sound toggle (no audio assets, kept for UI)
}


# ─────────────────────────────────────────────
#  LEADERBOARD
# ─────────────────────────────────────────────
def fetch_leaderboard():
    """Return list of entry dicts sorted by score descending."""
    if os.path.exists(LEADERBOARD_PATH):
        try:
            with open(LEADERBOARD_PATH, "r") as fp:
                payload = json.load(fp)
            if isinstance(payload, list):
                return payload
        except Exception:
            pass
    return []


def record_score(name: str, score: int, distance: int, coins: int):
    """Append a new entry and keep only the top 10."""
    roster = fetch_leaderboard()
    record = {
        "date":     datetime.now().strftime("%Y-%m-%d"),
        "coins":    coins,
        "distance": distance,
        "score":    score,
        "name":     name,
    }
    roster.append(record)
    roster.sort(key=lambda e: e["score"], reverse=True)
    roster = roster[:10]
    with open(LEADERBOARD_PATH, "w") as fp:
        json.dump(roster, fp, indent=2)
    return roster


# ─────────────────────────────────────────────
#  PREFERENCES
# ─────────────────────────────────────────────
def load_preferences():
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, "r") as fp:
                payload = json.load(fp)
            # Fill in any missing keys with defaults
            for pref_key, pref_value in DEFAULT_PREFERENCES.items():
                payload.setdefault(pref_key, pref_value)
            return payload
        except Exception:
            pass
    return dict(DEFAULT_PREFERENCES)


def save_preferences(preferences: dict):
    with open(SETTINGS_PATH, "w") as fp:
        json.dump(preferences, fp, indent=2)

