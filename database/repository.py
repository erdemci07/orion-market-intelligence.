from database.database import get_connection
from datetime import datetime, timedelta
from config import COOLDOWN_MINUTES

def add_log(level, message):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO logs (level, message)
        VALUES (?, ?)
        """,
        (level, message)
    )

    connection.commit()
    connection.close()
def add_or_update_watchlist(
    symbol,
    coin_score,
    market_score,
    sector_score,
    risk_score,
    confidence,
    decision,
    reason
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM watchlist
        WHERE symbol = ? AND status = 'WATCHING'
        """,
        (symbol,)
    )

    row = cursor.fetchone()

    if row:
        cursor.execute(
            """
            UPDATE watchlist
            SET coin_score = ?,
                market_score = ?,
                sector_score = ?,
                risk_score = ?,
                confidence = ?,
                decision = ?,
                reason = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                coin_score,
                market_score,
                sector_score,
                risk_score,
                confidence,
                decision,
                reason,
                row["id"]
            )
        )
    else:
        cursor.execute(
            """
            INSERT INTO watchlist (
                symbol,
                coin_score,
                market_score,
                sector_score,
                risk_score,
                confidence,
                decision,
                reason
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                symbol,
                coin_score,
                market_score,
                sector_score,
                risk_score,
                confidence,
                decision,
                reason
            )
        )

    connection.commit()
    connection.close()

from datetime import datetime, timedelta
from config import COOLDOWN_MINUTES


def is_symbol_in_cooldown(symbol):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT closed_at
        FROM positions
        WHERE symbol = ?
          AND status = 'CLOSED'
          AND closed_at IS NOT NULL
        ORDER BY closed_at DESC
        LIMIT 1
        """,
        (symbol,)
    )

    row = cursor.fetchone()
    connection.close()

    if not row:
        return False

    closed_at = datetime.fromisoformat(row["closed_at"])
    cooldown_until = closed_at + timedelta(minutes=COOLDOWN_MINUTES)

    return datetime.now() < cooldown_until


def get_active_watchlist():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM watchlist
        WHERE status = 'WATCHING'
    """)

    rows = cursor.fetchall()
    connection.close()

    return [dict(row) for row in rows]



def remove_from_watchlist(symbol):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE watchlist
        SET status = 'REMOVED',
            updated_at = CURRENT_TIMESTAMP
        WHERE symbol = ? AND status = 'WATCHING'
        """,
        (symbol,)
    )

    connection.commit()
    connection.close()

def partial_close_position(symbol, exit_price, close_ratio):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM positions
        WHERE symbol = ? AND status = 'OPEN'
        """,
        (symbol,)
    )

    position = cursor.fetchone()

    if not position:
        connection.close()
        return False

    position = dict(position)

    quantity = position["quantity"]
    close_quantity = quantity * close_ratio
    remaining_quantity = quantity - close_quantity

    entry_price = position["entry_price"]
    profit = (exit_price - entry_price) * close_quantity

    if remaining_quantity <= 0:
        cursor.execute(
            """
            UPDATE positions
            SET status = 'CLOSED',
                closed_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (position["id"],)
        )
    else:
        cursor.execute(
            """
            UPDATE positions
            SET quantity = ?
            WHERE id = ?
            """,
            (remaining_quantity, position["id"])
        )

    cursor.execute(
        """
        INSERT INTO trades (
            symbol,
            side,
            price,
            quantity,
            profit
        )
        VALUES (?, 'SELL', ?, ?, ?)
        """,
        (symbol, exit_price, close_quantity, profit)
    )

    connection.commit()
    connection.close()

    add_log(
        "INFO",
        f"{symbol} kısmi satış. Çıkış: {exit_price}, Miktar: {close_quantity}, Kâr: {profit}"
    )

    return True

def remove_from_watchlist(symbol):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE watchlist
        SET status = 'REMOVED',
            updated_at = CURRENT_TIMESTAMP
        WHERE symbol = ? AND status = 'WATCHING'
        """,
        (symbol,)
    )

    connection.commit()
    connection.close()

def get_open_positions():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM positions
        WHERE status = 'OPEN'
    """)

    rows = cursor.fetchall()
    connection.close()

    return [dict(row) for row in rows]


def has_open_position(symbol):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM positions
        WHERE symbol = ? AND status = 'OPEN'
        """,
        (symbol,)
    )

    row = cursor.fetchone()
    connection.close()

    return row is not None


def open_position(symbol, entry_price, quantity, score):
    if has_open_position(symbol):
        return False

    stop_price = entry_price * 0.95
    target_price = entry_price * 1.10

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO positions (
            symbol,
            entry_price,
            quantity,
            status,
            score,
            highest_price,
            stop_price,
            target_price
        )
        VALUES (?, ?, ?, 'OPEN', ?, ?, ?, ?)
        """,
        (
            symbol,
            entry_price,
            quantity,
            score,
            entry_price,
            stop_price,
            target_price
        )
    )

    cursor.execute(
        """
        INSERT INTO trades (
            symbol,
            side,
            price,
            quantity
        )
        VALUES (?, 'BUY', ?, ?)
        """,
        (symbol, entry_price, quantity)
    )

    connection.commit()
    connection.close()

    add_log("INFO", f"{symbol} pozisyon açıldı. Giriş: {entry_price}")
    return True


def update_position(symbol, updates):
    if not updates:
        return

    fields = []
    values = []

    for key, value in updates.items():
        fields.append(f"{key} = ?")
        values.append(value)

    values.append(symbol)

    query = f"""
        UPDATE positions
        SET {", ".join(fields)}
        WHERE symbol = ? AND status = 'OPEN'
    """

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(query, values)

    connection.commit()
    connection.close()


def close_position(symbol, exit_price):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM positions
        WHERE symbol = ? AND status = 'OPEN'
        """,
        (symbol,)
    )

    position = cursor.fetchone()

    if not position:
        connection.close()
        return False

    position = dict(position)

    entry_price = position["entry_price"]
    quantity = position["quantity"]

    profit = (exit_price - entry_price) * quantity

    cursor.execute(
        """
        UPDATE positions
        SET status = 'CLOSED',
            closed_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (position["id"],)
    )

    cursor.execute(
        """
        INSERT INTO trades (
            symbol,
            side,
            price,
            quantity,
            profit
        )
        VALUES (?, 'SELL', ?, ?, ?)
        """,
        (
            symbol,
            exit_price,
            quantity,
            profit
        )
    )

    connection.commit()
    connection.close()

    add_log("INFO", f"{symbol} pozisyon kapandı. Çıkış: {exit_price}, Kâr: {profit}")
    return True