import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
STATIC_FOLDER = os.path.join(BASE_DIR, 'static')
TEMPLATE_FOLDER = os.path.join(BASE_DIR, 'templates')
CREDENTIALS_SHEET = os.path.join(BASE_DIR, "credentials_for_copies.json")

SHEET_NAME = "test"
TAB_EXCHANGE = "Лист1"
TAB_COUNTRY_NAME = "страны"

CURRENCY_API_FOR_USD = "3b6770c8a71a4850b2faacbedcb8c0c7"
TG_API_KEY = "8345259625:AAGp8gV30HcZS_E0FKZ-pIA31RHfooty4PQ"
ADMINS = [5381172828]  # Список Telegram ID админов

URL_SITE = "https://oogenetic-factiously-joycelyn.ngrok-free.dev/"