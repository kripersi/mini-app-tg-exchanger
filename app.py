from flask import Flask, render_template, request, jsonify, flash
from datetime import datetime
from sql.sql import SQL
from sql.sql_model import Country, ExchangeRequest

app = Flask(__name__)
app.secret_key = "secret123"

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
        country_name = request.form.get('country')
        give_currency = request.form.get('give_currency')
        get_currency = request.form.get('get_currency')
        city = request.form.get('city')
        fullname = request.form.get('fullname', '').strip()
        email = request.form.get('email', '').strip()
        datetime_visit = request.form.get('datetime', '').strip()

        user_data = {
            "user_id": request.form.get("user_id"),
            "first_name": request.form.get("first_name"),
            "last_name": request.form.get("last_name"),
            "username": request.form.get("username")
        }

        errors = []
        country = db.get_country_by_name(country_name)

        if not country:
            errors.append("Неверная страна.")
        else:
            allowed = set(country.currencies_from_crypto + country.currencies_from_fiat)
            if give_currency not in allowed:
                errors.append("Недопустимая валюта (отдаете).")
            if get_currency not in allowed:
                errors.append("Недопустимая валюта (получаете).")
            if city not in country.cities:
                errors.append("Неверный город.")

        if give_currency == get_currency:
            errors.append("Нельзя обменивать одинаковые валюты!")
        if not fullname:
            errors.append("Введите ФИО.")
        if not email:
            errors.append("Введите почту.")
        if not datetime_visit:
            errors.append("Укажите дату и время визита.")

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template('form.html', countries=countries, form=request.form)

        try:
            visit_dt = datetime.fromisoformat(datetime_visit)
        except ValueError:
            flash("Неверный формат даты и времени.", "error")
            return render_template('form.html', countries=countries, form=request.form)

        req = ExchangeRequest(
            country_id=country.id,
            give_currency=give_currency,
            get_currency=get_currency,
            city=city,
            fullname=fullname,
            email=email,
            datetime=visit_dt,
            user_id=user_data.get("user_id"),
            first_name=user_data.get("first_name"),
            last_name=user_data.get("last_name"),
            username=user_data.get("username")
        )

        db.add_request(req)

        return render_template('success.html', data={
            "country": country_name,
            "give_currency": give_currency,
            "get_currency": get_currency,
            "city": city,
            "fullname": fullname,
            "email": email,
            "datetime": datetime_visit
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


if __name__ == '__main__':
    db = SQL()
    db.seed_countries()

    app.run(debug=True)
