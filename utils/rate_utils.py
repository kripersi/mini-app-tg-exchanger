from sqlalchemy import text
import re


def evaluate_formula(formula, price, buy_percent, sell_percent):
    """Подставляет значения в формулу из БД и вычисляет её."""
    expr = formula.format(price=price, buy=buy_percent, sell=sell_percent)
    expr = expr.replace("×", "*")
    expr = re.sub(r"\s+", "", expr)

    try:
        return eval(expr)
    except Exception:
        return None


def get_latest_rate(session, give, get):
    """Ищет подходящую пару в БД (прямая или обратная)."""
    query = text("""
        SELECT from_currency, to_currency, direction,
               buy_percent, sell_percent,
               buy_rate_formul, sell_rate_formul,
               price
        FROM exchange_rates
        WHERE from_currency ILIKE :give AND to_currency ILIKE :get
        ORDER BY updated_at DESC
        LIMIT 1
    """)

    # Прямая пара
    row = session.execute(query, {"give": f"%{give}%", "get": f"%{get}%"}).mappings().first()
    if row:
        return row, False

    # Обратная пара
    row = session.execute(query, {"give": f"%{get}%", "get": f"%{give}%"}).mappings().first()
    if row:
        return row, True

    return None, None


def find_best_rate(session, give, get):
    row, reversed_pair = get_latest_rate(session, give, get)
    if not row:
        return None

    direction = row["direction"]
    price = row["price"]
    buy_percent = row["buy_percent"]
    sell_percent = row["sell_percent"]
    buy_formula = row["buy_rate_formul"]
    sell_formula = row["sell_rate_formul"]

    # Прямая пара
    if not reversed_pair:
        if direction == "FIAT→CRYPTO":
            rate = evaluate_formula(sell_formula, price, buy_percent, sell_percent)
        elif direction == "CRYPTO→FIAT":
            rate = evaluate_formula(buy_formula, price, buy_percent, sell_percent)
        else:
            return None

    # Обратная пара
    else:
        if direction == "FIAT→CRYPTO":
            base_rate = evaluate_formula(sell_formula, price, buy_percent, sell_percent)
            rate = 1 / base_rate if base_rate else None
        elif direction == "CRYPTO→FIAT":
            base_rate = evaluate_formula(buy_formula, price, buy_percent, sell_percent)
            rate = 1 / base_rate if base_rate else None
        else:
            return None

    return {
        "rate": rate,
        "direction": direction,
        "reversed": reversed_pair
    }
