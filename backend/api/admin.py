from __future__ import annotations

from flask import Blueprint, jsonify, request, session

from ..auth import admin_required
from ..extensions import db
from ..models import User

admin_bp = Blueprint("admin", __name__)


@admin_bp.get("/users")
@admin_required
def list_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify([u.to_dict() for u in users]), 200


@admin_bp.patch("/users/<int:user_id>")
@admin_required
def patch_user(user_id: int):
    current_admin_id = session["user_id"]
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json(silent=True) or {}

    if "is_active" in data:
        if user_id == current_admin_id:
            return jsonify({"error": "Cannot change your own active status"}), 403
        value = data["is_active"]
        if not isinstance(value, bool):
            return jsonify({"error": "is_active must be a boolean"}), 400
        user.is_active = value

    db.session.commit()
    return jsonify(user.to_dict()), 200


@admin_bp.delete("/users/<int:user_id>")
@admin_required
def delete_user(user_id: int):
    current_admin_id = session["user_id"]
    if user_id == current_admin_id:
        return jsonify({"error": "Cannot delete your own account"}), 403

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    db.session.delete(user)
    db.session.commit()
    return "", 204
