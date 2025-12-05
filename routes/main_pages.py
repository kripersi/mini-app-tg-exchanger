from flask import Blueprint, render_template, request, flash, session as flask_session
from sql.sql_model import ExchangeRequest, TelegramUser
from utils.validation_utils import validate_form_data, validate_country_and_currencies, validate_amount_limits
from tg_bot import notify_admins
from extensions import db, bot_loop
from datetime import datetime
import asyncio

main_bp = Blueprint("main", __name__)


@main_bp.route('/')
def index():
    return render_template('index.html')


@main_bp.route('/cities')
def cities():
    countries = db.get_all_countries()
    return render_template('cities.html', countries=countries)


@main_bp.route('/rules')
def rules():
    return render_template('rules.html')


@main_bp.route('/about')
def about():
    return render_template('about.html')


@main_bp.route('/support')
def support():
    return render_template('support.html')


@main_bp.route("/cabinet")
def cabinet():
    return render_template("cabinet.html")


@main_bp.route("/history")
def history_page():
    return render_template("history.html")


@main_bp.route("/referral")
def referral_page():
    return render_template("referral.html")


@main_bp.route("/ref_program")
def ref_program_page():
    return render_template("ref_program.html")


@main_bp.route("/services")
def services_page():
    return render_template("services.html")


# ---------- ФОРМА ЗАЯВКИ ----------
@main_bp.route('/create', methods=['GET', 'POST'])
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
            "give_amount": form.get("give_amount"),
            "get_amount": form.get("get_amount"),
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
