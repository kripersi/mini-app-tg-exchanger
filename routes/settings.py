from flask import Blueprint, render_template, request, jsonify
from sql.sql_model import TelegramUser
from extensions import db

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/settings")
def settings():
    user_id = request.args.get("user_id")
    if not user_id:
        return "Пользователь не найден", 400

    user = db.get_user_by_tg_id(user_id)
    if not user:
        return "Пользователь не найден", 404

    return render_template("settings.html", user=user)


@settings_bp.route("/api/update_profile", methods=["POST"])
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
