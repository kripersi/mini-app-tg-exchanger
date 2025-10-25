from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, session
from datetime import datetime
from sql.sql import SQL
from sql.sql_model import Country, ExchangeRequest
from utils.rate_utils import find_best_rate
from utils.validation_utils import (
    validate_form_data,
    validate_country_and_currencies,
    validate_amount_limits
)
from utils.currency_utils import normalize_currency

# ---------- ИНИЦИАЛИЗАЦИЯ ----------
app = Flask(__name__)
app.secret_key = "secret123"

# Создаём экземпляр SQL
db = SQL()


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


# ---------- ФОРМА ЗАЯВКИ ----------
@app.route('/create', methods=['GET', 'POST'])
def create():
    countries = db.get_all_countries()

    if request.method == 'POST':
        form = request.form
        errors = []

        # 1. Базовая валидация данных формы
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

        # 3. Проверка курса и лимитов
        if not errors:
            amount_check = validate_amount_limits(db, form)
            if amount_check["errors"]:
                errors.extend(amount_check["errors"])
            else:
                give_amount = amount_check["amount"]

        # Если есть ошибки — возвращаем форму обратно
        if errors:
            for e in errors:
                flash(e, "error")
            return render_template('form.html', countries=countries, form=form)

        # 4. Сохранение заявки
        try:
            visit_dt = datetime.fromisoformat(form.get('datetime'))
        except ValueError:
            flash("Неверный формат даты и времени.", "error")
            return render_template('form.html', countries=countries, form=form)

        give_amount = float(form.get("give_amount").replace(",", "."))
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

        # Сохраняем данные в session и перенаправляем
        session["success_data"] = {
            "country": form.get('country'),
            "give_currency": form.get('give_currency'),
            "get_currency": form.get('get_currency'),
            "city": form.get('city'),
            "fullname": form.get('fullname'),
            "email": form.get('email'),
            "datetime": form.get('datetime')
        }

        return render_template('success.html', data={
            "country": form.get('country'),
            "give_currency": form.get('give_currency'),
            "get_currency": form.get('get_currency'),
            "city": form.get('city'),
            "fullname": form.get('fullname'),
            "email": form.get('email'),
            "datetime": form.get('datetime'),
            "user": {
                "id": form.get("user_id"),
                "first_name": form.get("first_name"),
                "last_name": form.get("last_name"),
                "username": form.get("username")
            }
        })

    return render_template('form.html', countries=countries)


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


# ---------- API: КУРСЫ ----------

@app.route("/get_rate")
def get_rate():
    give = request.args.get("give_currency")
    get = request.args.get("get_currency")

    if not give or not get:
        return jsonify({"error": "Укажите валюты"}), 400
    if give == get:
        return jsonify({"error": "Валюты не могут совпадать"}), 400

    give = normalize_currency(give)
    get = normalize_currency(get)

    with db.Session() as session:
        rate_data = find_best_rate(session, give, get)

        if not rate_data:
            return jsonify({"error": "Курс не найден"}), 404

        return jsonify(rate_data)


if __name__ == '__main__':
    db.seed_countries()
    app.run(debug=True)
