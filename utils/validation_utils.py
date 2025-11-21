from utils.rate_utils import find_best_rate


def validate_form_data(form):
    """Проверяет базовые поля формы."""
    errors = []
    required_fields = ["country", "give_currency", "get_currency", "city",
                       "fullname", "email", "datetime", "give_amount"]

    for field in required_fields:
        if not form.get(field):
            errors.append(f"Поле '{field}' обязательно для заполнения.")

    if form.get("give_currency") == form.get("get_currency"):
        errors.append("Нельзя обменивать одинаковые валюты.")

    return {"errors": errors}


def validate_country_and_currencies(db, form):
    """Проверяет корректность страны, валют и города."""
    errors = []
    country_name = form.get('country')
    give_currency = form.get('give_currency')
    get_currency = form.get('get_currency')
    city = form.get('city')

    country = db.get_country_by_name(country_name)
    if not country:
        return {"errors": ["Неверная страна."]}

    allowed = set(country.currencies_from_crypto + country.currencies_from_fiat)
    if give_currency not in allowed:
        errors.append("Недопустимая валюта (отдаёте).")
    if get_currency not in allowed:
        errors.append("Недопустимая валюта (получаете).")
    if city not in country.cities:
        errors.append("Неверный город.")

    return {"errors": errors, "country": country}


def validate_amount_limits(db, form):
    """Проверяет сумму через пересчёт в Cash USD."""
    errors = []
    try:
        amount = float(form.get('give_amount').replace(',', '.').strip())
    except (ValueError, AttributeError):
        return {"errors": ["Введите корректную сумму."]}

    give_currency = form.get("give_currency")
    min_usd = 5
    max_usd = 100000

    target_currency = "Cash USD"

    if give_currency == target_currency:
        usd_equivalent = amount
    else:
        with db.Session() as session:
            rate_data = find_best_rate(session, give_currency, target_currency)

            if not rate_data or not rate_data.get("rate"):
                return {"errors": [f"Не удалось получить курс к {target_currency}."]}

            usd_equivalent = amount * rate_data["rate"]

    if usd_equivalent < min_usd:
        errors.append(f"Сумма слишком мала: минимум {min_usd} USD (у вас {usd_equivalent:.4f} USD)")
    elif usd_equivalent > max_usd:
        errors.append(f"Сумма слишком большая: максимум {max_usd} USD (у вас {usd_equivalent:.2f} USD)")

    return {"errors": errors, "amount": amount}


