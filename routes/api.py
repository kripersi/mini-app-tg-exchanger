import json
import asyncio
from flask import Blueprint, jsonify, request
from aiogram.utils.deep_linking import create_start_link

from sqlalchemy import select
from sql.sql_model import TelegramUser, ExchangeRequest, ExchangeRate
from tg_bot import bot
from extensions import db, bot_loop
from utils.rate_utils import find_best_rate
from config import ADMINS

api_bp = Blueprint("api", __name__)


@api_bp.route('/api/country/<name>')
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


@api_bp.route("/get_possible_get_currencies")
def get_possible_get_currencies():
    give = request.args.get("give_currency")
    country_name = request.args.get("country")
    if not give:
        return jsonify({"currencies": []}), 400

    with db.Session() as session:
        rates = session.query(ExchangeRate).all()
        possible = set()

        for r in rates:
            if r.from_currency == give:
                possible.add(r.to_currency)
            elif r.to_currency == give:
                possible.add(r.from_currency)

    return jsonify({"currencies": sorted(possible)})


@api_bp.route("/get_rate")
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


@api_bp.route("/api/history/<user_id>")
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


@api_bp.route("/api/referral_link/<int:user_id>")
def referral_link(user_id):
    coro = create_start_link(bot, payload=str(user_id), encode=True)
    future = asyncio.run_coroutine_threadsafe(coro, bot_loop)
    try:
        link = future.result(timeout=5)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"link": link})


@api_bp.route("/api/referral/<user_id>")
def referral_info(user_id):
    with db.Session() as session:
        user = session.query(TelegramUser).filter_by(tg_id=str(user_id)).first()
        if not user:
            return jsonify({"count": 0, "list": []})
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


@api_bp.route("/api/user/<tg_id>")
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


@api_bp.route("/api/is_admin/<int:user_id>")
def is_admin(user_id):
    return jsonify({"admin": user_id in ADMINS})
