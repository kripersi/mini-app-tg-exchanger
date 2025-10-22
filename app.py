import json
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from config import *

app = Flask(
    __name__,
    static_folder=STATIC_FOLDER,
    template_folder=TEMPLATE_FOLDER
)


def load_exchange_data():
    """
    Открывает файл .json и возвращает dict с ключом 'data' распакованным.
    Если файл некорректен или нет ключа 'data' — возвращает пустой dict.
    """
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            payload = json.load(f)
        # ожидаем структуру { "data": { "США": {...}, ... } }
        if isinstance(payload, dict) and 'data' in payload and isinstance(payload['data'], dict):
            return payload['data']
        # если пользователь положил уже просто { "США": {...} }
        if isinstance(payload, dict):
            return payload
    except Exception as e:
        print("Ошибка загрузки exchange_data.json:", e)
    return {}


def save_request(payload: dict):
    requests = []
    if os.path.exists(REQUESTS_FILE):
        with open(REQUESTS_FILE, 'r', encoding='utf-8') as f:
            try:
                requests = json.load(f)
            except json.JSONDecodeError:
                requests = []
    requests.append(payload)
    with open(REQUESTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(requests, f, ensure_ascii=False, indent=2)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/cities')
def cities():
    countries = {
        "США": ["New York", "Los Angeles", "Houston"],
        "Индия": ["Delhi", "Mumbai", "Bangalore"],
        "Япония": ["Tokyo", "Osaka", "Kyoto"]
    }
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


@app.route('/create', methods=['GET', 'POST'])
def create():
    data = load_exchange_data()
    countries = list(data.keys())

    if request.method == 'POST':
        country = request.form.get('country')
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

        # проверка страны
        if country not in data:
            errors.append("Выбрана неверная страна.")
        else:
            crypto = data[country].get("currencies_from_crypto", [])
            fiat = data[country].get("currencies_from_fiat", [])
            allowed_currencies = set(crypto + fiat)
            allowed_cities = set(data[country]["cities"])

            if give_currency not in allowed_currencies:
                errors.append("Недопустимая валюта (отдаете).")
            if get_currency not in allowed_currencies:
                errors.append("Недопустимая валюта (получаете).")
            if city not in allowed_cities:
                errors.append("Неверный город для этой страны.")

        # новая проверка: нельзя обменять одинаковые валюты
        if give_currency == get_currency and give_currency is not None:
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
            return render_template('form.html', countries=countries, data=data, form=request.form)

        payload = {
            "country": country,
            "give_currency": give_currency,
            "get_currency": get_currency,
            "city": city,
            "fullname": fullname,
            "email": email,
            "datetime": datetime_visit,
            "user": user_data
        }

        save_request(payload)
        return render_template('success.html', data=payload)

    return render_template('form.html', countries=countries, data=data)


@app.route('/api/country/<country>')
def get_country_data(country):
    data = load_exchange_data()

    if country not in data:
        return jsonify({"error": "Страна не найдена", "available": list(data.keys())}), 404

    country_data = data[country]
    return jsonify({
        "code": country_data.get("code"),
        "cities": country_data.get("cities", []),
        "currencies_from_crypto": country_data.get("currencies_from_crypto", []),
        "currencies_from_fiat": country_data.get("currencies_from_fiat", [])
    })


if __name__ == '__main__':
    app.run(debug=True)
