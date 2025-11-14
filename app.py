from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, session
from datetime import datetime

import asyncio
from tg_bot import notify_admins, bot
from aiogram.utils.deep_linking import create_start_link

from sql.sql import SQL
from sql.sql_model import Country, ExchangeRequest, Referral
from sqlalchemy import select

from utils.rate_utils import find_best_rate
from utils.validation_utils import (
    validate_form_data,
    validate_country_and_currencies,
    validate_amount_limits
)

from config import NAME_BOT

# ---------- ИНИЦИАЛИЗАЦИЯ ----------
app = Flask(__name__)
app.secret_key = "secret123"

# Создаём экземпляр SQL
db = SQL()

# dfs
import asyncio
import threading

# создаём отдельный event loop
bot_loop = asyncio.new_event_loop()

def start_bot_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

# запускаем event loop в фоне
threading.Thread(target=start_bot_loop, args=(bot_loop,), daemon=True).start()

# ---------- СТРАНИЦЫ ----------

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/cities')
def cities():
    countries = db.get_all_countries()
    return render_template('cities.html', countries=countries)


@app.route('/rules')
def rules():
    return render_template('rules.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/support')
def support():
    return render_template('support.html')


@app.route("/cabinet")
def cabinet():
    return render_template("cabinet.html")


@app.route("/history")
def history_page():
    return render_template("history.html")


@app.route("/referral")
def referral_page():
    return render_template("referral.html")


# ---------- ФОРМА ЗАЯВКИ ----------
@app.route('/create', methods=['GET', 'POST'])
def create():
    countries = db.get_all_countries()

    if request.method == 'POST':
        form = request.form
        errors = []

        # 1. Базовая валидация
        validated = validate_form_data(form)
        if validated["errors"]:
            errors.extend(validated["errors"])

        # 2. Проверка страны, валют и города
        if not errors:
            country_check = validate_country_and_currencies(db, form)
            if country_check["errors"]:
                errors.extend(country_check["errors"])
            else:
                country = country_check["country"]

        # 3. Проверка лимитов
        if not errors:
            amount_check = validate_amount_limits(db, form)
            if amount_check["errors"]:
                errors.extend(amount_check["errors"])
            else:
                give_amount = amount_check["amount"]

        # 4. Обработка ошибок
        if errors:
            for e in errors:
                flash(e, "error")
            return render_template('form.html', countries=countries, form=form)

        # 5. Сохранение заявки
        try:
            visit_dt = datetime.fromisoformat(form.get('datetime'))
        except ValueError:
            flash("Неверный формат даты и времени.", "error")
            return render_template('form.html', countries=countries, form=form)

        get_amount = float(form.get("get_amount").replace(",", "."))
        req = ExchangeRequest(
            country_id=country.id,
            give_currency=form.get("give_currency"),
            get_currency=form.get("get_currency"),
            give_amount=give_amount,
            get_amount=get_amount,
            city=form.get("city"),
            fullname=form.get("fullname"),
            email=form.get("email"),
            datetime=form.get("datetime"),
            user_id=form.get("user_id"),
            first_name=form.get("first_name"),
            last_name=form.get("last_name"),
            username=form.get("username")
        )

        db.add_request(req)

        # 6. Формирование и отправка уведомления
        data = {
                "country": form.get("country"),
                "give_currency": form.get("give_currency"),
                "get_currency": form.get("get_currency"),
                "city": form.get("city"),
                "fullname": form.get("fullname"),
                "email": form.get("email"),
                "datetime": form.get("datetime"),
                "user": {
                    "id": form.get("user_id"),
                    "first_name": form.get("first_name"),
                    "last_name": form.get("last_name"),
                    "username": form.get("username")
                }
            }
        asyncio.run(notify_admins(data))

        # 7. Отображение успеха
        session["success_data"] = data
        return render_template("success.html", data=data)

    return render_template("form.html", countries=countries)


# ---------- API ----------
@app.route('/api/country/<name>')
def get_country(name):
    country = db.get_country_by_name(name)
    if not country:
        return jsonify({"error": "Страна не найдена"}), 404

    return jsonify({
        "name": country.name,
        "code": country.code,
        "currencies_from_crypto": country.currencies_from_crypto,
        "currencies_from_fiat": country.currencies_from_fiat,
        "cities": country.cities
    })


@app.route("/get_rate")
def get_rate():
    give = request.args.get("give_currency")
    get = request.args.get("get_currency")

    if not give or not get:
        return jsonify({"error": "Укажите валюты"}), 400
    if give == get:
        return jsonify({"error": "Валюты не могут совпадать"}), 400

    with db.Session() as session:
        rate_data = find_best_rate(session, give, get)

        if not rate_data:
            return jsonify({"error": "Курс не найден"}), 404

        return jsonify(rate_data)


@app.route("/api/history/<user_id>")
def history(user_id):
    with db.Session() as session:
        stmt = (
            select(ExchangeRequest)
            .where(ExchangeRequest.user_id == user_id)
            .order_by(ExchangeRequest.id.desc())
        )
        data = session.execute(stmt).scalars().all()

        out = []
        for r in data:
            out.append({
                "id": r.id,
                "status": r.status,
                "give_amount": r.give_amount,
                "give_currency": r.give_currency,
                "get_amount": r.get_amount,
                "get_currency": r.get_currency,
                "datetime": r.datetime.strftime("%Y-%m-%d %H:%M"),
                "city": r.city
            })

        return jsonify(out)


@app.route("/api/referral_link/<int:user_id>")
def referral_link(user_id):
    coro = create_start_link(bot, payload=str(user_id), encode=True)
    future = asyncio.run_coroutine_threadsafe(coro, bot_loop)

    try:
        link = future.result(timeout=5)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"link": link})


@app.route("/api/referral/<user_id>")
def referral_info(user_id):
    with db.Session() as session:
        # Запрос на получение рефералов для данного пользователя
        stmt = (
            select(Referral)
            .where(Referral.user_id == user_id)
            .order_by(Referral.id.desc())
        )
        referrals = session.execute(stmt).scalars().all()

        # Формирование списка рефералов
        list_out = []
        for r in referrals:
            list_out.append({
                "invited_id": r.invited_id,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M")  # Преобразуем дату в строку
            })

        # Возвращаем данные в формате JSON
        return jsonify({
            "link": f"https://t.me/{NAME_BOT}?start=ref_{user_id}",
            "count": len(referrals),  # Количество приглашённых
            "list": list_out  # Список приглашённых
        })


if __name__ == '__main__':
    db.seed_countries()
    app.run(debug=True)
