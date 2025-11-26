from sqlalchemy import text
import re


def evaluate_formula(formula, price, buy_percent, sell_percent):
    """Подставляет значения в формулу и вычисляет её."""
    expr = formula.format(price=price, buy=buy_percent, sell=sell_percent)
    expr = expr.replace("×", "*")
    expr = re.sub(r"\s+", "", expr)
    try:
        return eval(expr)
    except Exception:
        return None


def get_latest_rate(session, give_code, get_code):
    """
    Ищет подходящую пару по коду валюты.
    Возвращает row и флаг reversed_pair.
    """
    query = text("""
        SELECT from_currency, to_currency, direction,
               buy_percent, sell_percent,
               buy_rate_formul, sell_rate_formul,
               price
        FROM exchange_rates
        WHERE from_currency ILIKE '%' || :give || '%' AND to_currency ILIKE '%' || :get || '%'
        ORDER BY updated_at DESC
        LIMIT 1
    """)

    # Прямая пара
    row = session.execute(query, {"give": give_code, "get": get_code}).mappings().first()
    if row:
        return row, False

    # Обратная пара
    row = session.execute(query, {"give": get_code, "get": give_code}).mappings().first()
    if row:
        return row, True

    return None, None


def find_best_rate(session, give_code, get_code):
    # Пробуем прямой курс или обратный
    row, reversed_pair = get_latest_rate(session, give_code, get_code)
    if row:
        return _compute_rate_from_row(row, reversed_pair)

    intermediary = "Tether TRC20 (USDT)"

    # A → USDT
    row1, rev1 = get_latest_rate(session, give_code, intermediary)
    # USDT → B
    row2, rev2 = get_latest_rate(session, intermediary, get_code)

    if row1 and row2:
        rate1 = _compute_rate_value(row1, rev1)
        rate2 = _compute_rate_value(row2, rev2)

        if rate1 and rate2:
            return {
                "rate": rate1 * rate2,
                "direction": "via_usdt",
                "reversed": False
            }

    return None


# вспомогательная функция для обработки строки курса
def _compute_rate_from_row(row, reversed_pair):
    direction = row["direction"]
    price = row["price"]
    buy_percent = row["buy_percent"]
    sell_percent = row["sell_percent"]
    buy_formula = row["buy_rate_formul"]
    sell_formula = row["sell_rate_formul"]

    if not reversed_pair:

        # Прямая пара
        if direction == "FIAT→CRYPTO":
            rate = evaluate_formula(sell_formula, price, buy_percent, sell_percent)

        elif direction == "CRYPTO→FIAT":
            rate = evaluate_formula(buy_formula, price, buy_percent, sell_percent)

        elif direction == "CRYPTO→CRYPTO":
            rate = evaluate_formula(sell_formula, price, buy_percent, sell_percent)

        else:
            return None

    else:

        # Реверс пары
        if direction == "FIAT→CRYPTO":
            base = evaluate_formula(sell_formula, price, buy_percent, sell_percent)
        elif direction == "CRYPTO→FIAT":
            base = evaluate_formula(buy_formula, price, buy_percent, sell_percent)

        elif direction == "CRYPTO→CRYPTO":
            base = evaluate_formula(sell_formula, price, buy_percent, sell_percent)
        else:
            return None

        rate = 1 / base if base else None

    return {
        "rate": rate,
        "direction": direction,
        "reversed": reversed_pair
    }


# вычисляет курс без упаковки в dict
def _compute_rate_value(row, reversed_pair):
    result = _compute_rate_from_row(row, reversed_pair)
    return result["rate"] if result else None
