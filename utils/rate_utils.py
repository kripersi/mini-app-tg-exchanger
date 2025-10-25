from sqlalchemy import text


def get_latest_rate(session, pair):
    """Возвращает последнюю запись по валютной паре."""
    query = text("""
        SELECT rate
        FROM exchange_rates
        WHERE pair = :pair
        ORDER BY updated_at DESC
        LIMIT 1
    """)
    return session.execute(query, {"pair": pair}).mappings().first()


def find_best_rate(session, give, get, bridge="USDT"):
    if give == get:
        return None

    pair = f"{give}/{get}"
    reverse_pair = f"{get}/{give}"

    # Прямой курс
    row = get_latest_rate(session, pair)
    if row and row["rate"]:
        return {"rate": row["rate"]}

    # Обратный курс (инвертируем)
    row = get_latest_rate(session, reverse_pair)
    if row and row["rate"]:
        rate = 1 / row["rate"]
        return {"rate": rate}

    # Через мост (give → bridge → get)
    if bridge not in [give, get]:
        give_to_bridge = get_latest_rate(session, f"{give}/{bridge}")
        bridge_to_get = get_latest_rate(session, f"{bridge}/{get}")
        if give_to_bridge and bridge_to_get:
            rate = give_to_bridge["rate"] * bridge_to_get["rate"]
            return {"rate": rate}

    # Через мост, если одна из валют = мост (например, USDT→ETH или ETH→USDT)
    # USDT→ETH (используем ETH/USDT)
    if give == bridge:
        direct = get_latest_rate(session, f"{get}/{bridge}")
        if direct and direct["rate"]:
            rate = 1 / direct["rate"]
            return {"rate": rate}

    # ETH→USDT
    if get == bridge:
        direct = get_latest_rate(session, f"{bridge}/{give}")
        if direct and direct["rate"]:
            return {"rate": direct["rate"]}

    # Через мост, если есть оба направления (give->bridge и get->bridge)
    give_to_bridge = get_latest_rate(session, f"{give}/{bridge}")
    get_to_bridge = get_latest_rate(session, f"{get}/{bridge}")
    if give_to_bridge and get_to_bridge:
        rate = give_to_bridge["rate"] / get_to_bridge["rate"]
        return {"rate": rate}

    return None



