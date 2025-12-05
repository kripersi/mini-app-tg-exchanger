import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
STATIC_FOLDER = os.path.join(BASE_DIR, 'static')
TEMPLATE_FOLDER = os.path.join(BASE_DIR, 'templates')
CREDENTIALS_SHEET = os.path.join(BASE_DIR, "credentials_for_copies.json")

SHEET_NAME = "test"
TAB_EXCHANGE = "Лист1"
TAB_COUNTRY_NAME = "страны"

TG_API_KEY = os.getenv("TG_API_KEY")
ADMINS = [...]  # Список Telegram ID админов

URL_SITE = "https://...../"
