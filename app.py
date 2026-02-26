from flask import Flask
from config import ADMINS
from extensions import db
from routes.main_pages import main_bp
from routes.admin import admin_bp
from routes.api import api_bp
from routes.settings import settings_bp

app = Flask(__name__)
app.secret_key = "secret123"

# Регистрация blueprints
app.register_blueprint(main_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(api_bp)
app.register_blueprint(settings_bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
