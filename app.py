from flask import Flask
from config import ADMINS
from extensions import db, bot_loop
import threading

app = Flask(__name__)
app.secret_key = "secret123"


def start_bot_loop(loop):
    import asyncio
    asyncio.set_event_loop(loop)
    loop.run_forever()


threading.Thread(target=start_bot_loop, args=(bot_loop,), daemon=True).start()

# Импортируем Blueprints после создания app и db
from routes.main_pages import main_bp
from routes.admin import admin_bp
from routes.api import api_bp
from routes.settings import settings_bp

app.register_blueprint(main_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(api_bp)
app.register_blueprint(settings_bp)

if __name__ == '__main__':
    db.seed_countries()
    app.run(host="0.0.0.0", port=5000, debug=True)
