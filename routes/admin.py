from flask import Blueprint, render_template, request, redirect
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from sql.sql_model import ExchangeRequest, TelegramUser
from extensions import db
from config import ADMINS

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("")
def admin_panel():
    user_id = request.args.get("user_id", type=int)
    if not user_id or user_id not in ADMINS:
        return "Access denied", 403
    return render_template("admin_panel.html")


@admin_bp.route("/requests")
def admin_requests():
    user_id = request.args.get("user_id", type=int)
    if not user_id or user_id not in ADMINS:
        return "Access denied", 403
    with db.Session() as session:
        requests_list = session.execute(
            select(ExchangeRequest.id).order_by(ExchangeRequest.id.desc())
        ).scalars().all()
    return render_template("admin_requests.html", reqs=requests_list)


@admin_bp.route("/users")
def admin_users():
    user_id = request.args.get("user_id", type=int)
    if not user_id or user_id not in ADMINS:
        return "Access denied", 403
    with db.Session() as session:
        users = session.execute(
            select(TelegramUser).order_by(TelegramUser.id.desc())
        ).scalars().all()
    return render_template("admin_users.html", users=users)


@admin_bp.route("/user/<int:user_id_view>")
def admin_user_view(user_id_view):
    user_id = request.args.get("user_id", type=int)
    if not user_id or user_id not in ADMINS:
        return "Access denied", 403
    with db.Session() as session:
        u = session.get(TelegramUser, user_id_view)
        if not u:
            return "Пользователь не найден", 404
    return render_template("admin_user_view.html", u=u)


@admin_bp.route("/user/<int:user_id_view>/ban", methods=["POST"])
def admin_user_ban(user_id_view):
    user_id = request.args.get("user_id", type=int)
    if not user_id or user_id not in ADMINS:
        return "Access denied", 403
    with db.Session() as session:
        u = session.get(TelegramUser, user_id_view)
        if not u:
            return "Пользователь не найден", 404
        u.banned = False if u.banned else True
        session.commit()
    return redirect(f"/admin/user/{user_id_view}?user_id={user_id}")


@admin_bp.route("/request/<int:req_id>")
def admin_request_view(req_id):
    user_id = request.args.get("user_id", type=int)
    if not user_id or user_id not in ADMINS:
        return "Access denied", 403
    with db.Session() as session:
        req = session.execute(
            select(ExchangeRequest)
            .options(selectinload(ExchangeRequest.country_data))
            .where(ExchangeRequest.id == req_id)
        ).scalar_one_or_none()
        if not req:
            return "Заявка не найдена", 404
    return render_template("admin_request_view.html", req=req)


@admin_bp.route("/request/<int:req_id>/status", methods=["POST"])
def admin_update_status(req_id):
    user_id = request.args.get("user_id", type=int)
    if not user_id or user_id not in ADMINS:
        return "Access denied", 403
    new_status = request.form.get("status")
    with db.Session() as session:
        req = session.get(ExchangeRequest, req_id)
        if not req:
            return "Заявка не найдена", 404
        req.status = new_status
        session.commit()
    return redirect(f"/admin/request/{req_id}?user_id={user_id}")
