import json

from flask import Flask, render_template, request, jsonify, flash, redirect
from datetime import datetime
from flask import session as flask_session

from tg_bot import notify_admins, bot
from aiogram.utils.deep_linking import create_start_link

from sql.sql import SQL
from sql.sql_model import Country, ExchangeRequest, TelegramUser
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from utils.rate_utils import find_best_rate
from utils.validation_utils import (
    validate_form_data,
    validate_country_and_currencies,
    validate_amount_limits
)

from config import ADMINS

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


# ---------- АДМИН ----------
@app.route("/admin")
def admin_panel():
    user_id = request.args.get("user_id", type=int)

    if not user_id:
        return "Access denied: missing user_id", 403

    if user_id not in ADMINS:
        return "Access denied: you are not admin", 403

    return render_template("admin_panel.html")


# ---------- АДМИН: заявки ----------
@app.route("/admin/requests")
def admin_requests():
    user_id = request.args.get("user_id", type=int)
    if not user_id or user_id not in ADMINS:
        return "Access denied", 403

    with db.Session() as session:
        requests_list = session.execute(
            select(ExchangeRequest.id).order_by(ExchangeRequest.id.desc())
        ).scalars().all()

    return render_template("admin_requests.html", reqs=requests_list)


# ---------- АДМИН: пользователи ----------
@app.route("/admin/users")
def admin_users():
    user_id = request.args.get("user_id", type=int)
    if not user_id or user_id not in ADMINS:
        return "Access denied", 403

    with db.Session() as session:
        users = session.execute(
            select(TelegramUser).order_by(TelegramUser.id.desc())
        ).scalars().all()

    return render_template("admin_users.html", users=users)


@app.route("/admin/user/<int:user_id_view>")
def admin_user_view(user_id_view):
    user_id = request.args.get("user_id", type=int)
    if not user_id or user_id not in ADMINS:
        return "Access denied", 403

    with db.Session() as session:
        u = session.get(TelegramUser, user_id_view)
        if not u:
            return "Пользователь не найден", 404

    return render_template("admin_user_view.html", u=u)


@app.route("/admin/user/<int:user_id_view>/ban", methods=["POST"])
def admin_user_ban(user_id_view):
    user_id = request.args.get("user_id", type=int)
    if not user_id or user_id not in ADMINS:
        return "Access denied", 403

    with db.Session() as session:
        u = session.get(TelegramUser, user_id_view)
        if not u:
            return "Пользователь не найден", 404

        u.banned = False if u.banned else True
        session.commit()

    return redirect(f"/admin/user/{user_id_view}?user_id={user_id}")


@app.route("/admin/request/<int:req_id>")
def admin_request_view(req_id):
    user_id = request.args.get("user_id", type=int)
    if not user_id or user_id not in ADMINS:
        return "Access denied", 403

    with db.Session() as session:
        req = session.execute(
            select(ExchangeRequest)
            .options(selectinload(ExchangeRequest.country_data))
            .where(ExchangeRequest.id == req_id)
        ).scalar_one_or_none()

        if not req:
            return "Заявка не найдена", 404

    return render_template("admin_request_view.html", req=req)


@app.route("/admin/request/<int:req_id>/status", methods=["POST"])
def admin_update_status(req_id):
    user_id = request.args.get("user_id", type=int)
    if not user_id or user_id not in ADMINS:
        return "Access denied", 403

    new_status = request.form.get("status")

    with db.Session() as session:
        req = session.get(ExchangeRequest, req_id)
        if not req:
            return "Заявка не найдена", 404

        req.status = new_status
        session.commit()

    return redirect(f"/admin/request/{req_id}?user_id={user_id}")


# ---------- ФОРМА ЗАЯВКИ ----------
@app.route('/create', methods=['GET', 'POST'])
def create():
    countries = db.get_all_countries()

    if request.method == 'POST':
        form = request.form
        errors = []

        # 0. Проверка — заблокирован ли пользователь
        user_id = form.get("user_id")
        with db.Session() as session:
            user = session.query(TelegramUser).filter_by(tg_id=user_id).first()

            if user and user.banned:
                flash("Ваш аккаунт заблокирован. Вы не можете создавать заявки.", "error")
                return render_template("form.html", countries=countries, form=form)

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

        # 4. Если есть ошибки — показываем форму снова
        if errors:
            for e in errors:
                flash(e, "error")
            return render_template('form.html', countries=countries, form=form)

        # 5. Парсим дату
        try:
            visit_dt = datetime.fromisoformat(form.get('datetime'))
        except ValueError:
            flash("Неверный формат даты и времени.", "error")
            return render_template('form.html', countries=countries, form=form)

        # 6. Сохранение заявки
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

        # 7. Отправка уведомления админу
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

        # 8. Показываем страницу успеха
        flask_session["success_data"] = data
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
        user = session.query(TelegramUser).filter_by(tg_id=str(user_id)).first()
        if not user:
            return jsonify({"count": 0, "list": []})

        # Загружаем JSON-массив
        referrals = json.loads(user.referrals or "[]")

        list_out = []
        for r_id in referrals:
            ref_user = session.query(TelegramUser).filter_by(tg_id=str(r_id)).first()
            list_out.append({
                "invited_id": r_id,
                "username": ref_user.username if ref_user else None,
                "first_name": ref_user.first_name if ref_user else None,
                "last_name": ref_user.last_name if ref_user else None,
                "first_start": ref_user.first_start.strftime("%Y-%m-%d %H:%M") if ref_user else None
            })

        return jsonify({
            "count": len(referrals),
            "list": list_out
        })


@app.route("/api/user/<tg_id>")
def api_get_user(tg_id):
    user = db.get_user_by_tg_id(tg_id)
    if not user:
        return {"error": "user_not_found"}, 404

    return {
        "tg_id": user.tg_id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": user.full_name or "",
        "email": user.email or ""
    }


@app.route("/api/is_admin/<int:user_id>")
def is_admin(user_id):
    return jsonify({"admin": user_id in ADMINS})


# ---------- ЛИЧНЫЕ НАСТРОЙКИ ----------
@app.route("/settings")
def settings():
    user_id = request.args.get("user_id")
    if not user_id:
        return "Пользователь не найден", 400

    user = db.get_user_by_tg_id(user_id)
    if not user:
        return "Пользователь не найден", 404

    return render_template("settings.html", user=user)


@app.route("/api/update_profile", methods=["POST"])
def update_profile():
    tg_id = request.form.get("user_id")
    full_name = request.form.get("full_name")
    email = request.form.get("email")

    if not tg_id:
        return jsonify({"error": "user_id is required"}), 400

    with db.Session() as session:
        user = session.query(TelegramUser).filter_by(tg_id=str(tg_id)).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        user.full_name = full_name
        user.email = email

        session.commit()

    return jsonify({"success": True})


if __name__ == '__main__':
    db.seed_countries()
    app.run(debug=True)
