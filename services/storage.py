import json
from pathlib import Path


POSITIONS_FILE = Path("positions.json")


def load_positions():
    if not POSITIONS_FILE.exists():
        return []

    try:
        with open(POSITIONS_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError:
        return []


def save_positions(positions):
    with open(POSITIONS_FILE, "w", encoding="utf-8") as file:
        json.dump(positions, file, indent=4, ensure_ascii=False)


def get_open_positions():
    return [
        p for p in load_positions()
        if p.get("status") == "OPEN"
    ]


def add_position(position):
    positions = load_positions()

    for p in positions:
        if p["symbol"] == position["symbol"] and p["status"] == "OPEN":
            return False

    positions.append(position)
    save_positions(positions)
    return True


def update_position(symbol, updates):
    positions = load_positions()

    for p in positions:
        if p["symbol"] == symbol and p["status"] == "OPEN":
            p.update(updates)

    save_positions(positions)


def close_position(symbol):
    update_position(symbol, {"status": "CLOSED"})