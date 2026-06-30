import json
from pathlib import Path


POSITIONS_FILE = Path("positions.json")


def load_positions():
    if not POSITIONS_FILE.exists():
        return []

    with open(POSITIONS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_positions(positions):
    with open(POSITIONS_FILE, "w", encoding="utf-8") as file:
        json.dump(positions, file, indent=4, ensure_ascii=False)


def add_position(symbol, entry_price, quantity, score):
    positions = load_positions()

    for position in positions:
        if position["symbol"] == symbol and position["status"] == "OPEN":
            return False

    positions.append({
        "symbol": symbol,
        "entry_price": entry_price,
        "quantity": quantity,
        "score": score,
        "status": "OPEN"
    })

    save_positions(positions)
    return True


def close_position(symbol):
    positions = load_positions()

    for position in positions:
        if position["symbol"] == symbol and position["status"] == "OPEN":
            position["status"] = "CLOSED"

    save_positions(positions)


def get_open_positions():
    positions = load_positions()
    return [p for p in positions if p["status"] == "OPEN"]