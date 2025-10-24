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
    pair = f"{give}/{get}"
    reverse_pair = f"{get}/{give}"

    # Прямой курс
    row = get_latest_rate(session, pair)
    if row and row["rate"]:
        return {"rate": row["rate"]}

    # Обратный курс — инвертируем
    row = get_latest_rate(session, reverse_pair)
    if row and row["rate"]:
        rate = 1 / row["rate"]
        return {"rate": rate}

    # Через мост — give → bridge → get
    give_to_bridge = get_latest_rate(session, f"{give}/{bridge}")
    bridge_to_get = get_latest_rate(session, f"{bridge}/{get}")
    if give_to_bridge and bridge_to_get:
        return {"rate": give_to_bridge["rate"] * bridge_to_get["rate"]}

    # Через мост — bridge → give и get → bridge
    bridge_to_give = get_latest_rate(session, f"{bridge}/{give}")
    get_to_bridge = get_latest_rate(session, f"{get}/{bridge}")
    if bridge_to_give and get_to_bridge:
        return {"rate": (1 / bridge_to_give["rate"]) * (1 / get_to_bridge["rate"])}

    # Через мост — give → bridge и get → bridge
    give_to_bridge = get_latest_rate(session, f"{give}/{bridge}")
    get_to_bridge = get_latest_rate(session, f"{get}/{bridge}")
    if give_to_bridge and get_to_bridge:
        return {"rate": give_to_bridge["rate"] / get_to_bridge["rate"]}

    return None


