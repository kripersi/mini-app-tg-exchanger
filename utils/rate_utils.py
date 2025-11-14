from sqlalchemy import text


def get_latest_rate(session, pair):
    """Возвращает курс по валютной паре, включая инверсию, если прямой пары нет."""
    # Прямой запрос
    query = text("""
        SELECT rate
        FROM exchange_rates
        WHERE pair = :pair
        ORDER BY updated_at DESC
        LIMIT 1
    """)
    row = session.execute(query, {"pair": pair}).mappings().first()
    if row:
        return {"rate": row["rate"]}

    # Попробуем обратную пару
    base, quote = pair.split("/")
    reverse_pair = f"{quote}/{base}"
    reverse_row = session.execute(query, {"pair": reverse_pair}).mappings().first()
    if reverse_row and reverse_row["rate"]:
        return {"rate": 1 / reverse_row["rate"]}

    return None


def find_best_rate(session, give, get, bridge="USDT"):
    if give == get:
        return None

    # Обработка эквивалентных валют
    equivalent = {
        ("USD", "USDT"): 1.0,
        ("USDT", "USD"): 1.0
    }
    if (give, get) in equivalent:
        return {"rate": equivalent[(give, get)]}

    # Заменяем эквиваленты на мостовую валюту для дальнейших расчётов
    give_normalized = "USDT" if give == "USD" else give
    get_normalized = "USDT" if get == "USD" else get

    pair = f"{give_normalized}/{get_normalized}"
    reverse_pair = f"{get_normalized}/{give_normalized}"

    # Прямой курс
    row = get_latest_rate(session, pair)
    if row and row["rate"]:
        return {"rate": row["rate"]}

    # Обратный курс
    row = get_latest_rate(session, reverse_pair)
    if row and row["rate"]:
        return {"rate": 1 / row["rate"]}

    # Через мост
    if bridge not in [give_normalized, get_normalized]:
        give_to_bridge = get_latest_rate(session, f"{give_normalized}/{bridge}")
        bridge_to_get = get_latest_rate(session, f"{bridge}/{get_normalized}")
        if give_to_bridge and bridge_to_get:
            rate = give_to_bridge["rate"] * bridge_to_get["rate"]
            return {"rate": rate}

    # Через мост, если одна из валют = мост
    if give_normalized == bridge:
        direct = get_latest_rate(session, f"{get_normalized}/{bridge}")
        if direct and direct["rate"]:
            return {"rate": 1 / direct["rate"]}

    if get_normalized == bridge:
        direct = get_latest_rate(session, f"{bridge}/{give_normalized}")
        if direct and direct["rate"]:
            return {"rate": direct["rate"]}

    # Через мост, если есть оба направления
    give_to_bridge = get_latest_rate(session, f"{give_normalized}/{bridge}")
    get_to_bridge = get_latest_rate(session, f"{get_normalized}/{bridge}")
    if give_to_bridge and get_to_bridge:
        rate = give_to_bridge["rate"] / get_to_bridge["rate"]
        return {"rate": rate}

    return None




