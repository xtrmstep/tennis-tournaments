from __future__ import annotations

from datetime import datetime, timezone

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

    if "is_moderator" in data:
        value = data["is_moderator"]
        if not isinstance(value, bool):
            return jsonify({"error": "is_moderator must be a boolean"}), 400
        user.is_moderator = value

    db.session.commit()
    return jsonify(user.to_dict()), 200


@admin_bp.patch("/users/<int:user_id>/skill")
@admin_required
def update_user_skill(user_id: int):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json(silent=True) or {}
    skill_level = data.get("skill_level")

    if (
        skill_level is None
        or isinstance(skill_level, bool)
        or not isinstance(skill_level, int)
        or not (0 <= skill_level <= 10)
    ):
        return jsonify({"error": "skill_level must be an integer from 0 to 10"}), 400

    user.skill_level = skill_level
    user.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify({"id": user.id, "skill_level": user.skill_level}), 200


@admin_bp.put("/users/<int:user_id>/profile")
@admin_required
def update_user_profile(user_id: int):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    full_name = (data.get("full_name") or "").strip()
    username = (data.get("username") or "").strip()
    skill_level = data.get("skill_level")
    gender = (data.get("gender") or "").strip()

    if not email or "@" not in email:
        return jsonify({"error": "Valid email is required"}), 400
    if not full_name:
        return jsonify({"error": "Full name is required"}), 400
    if not username:
        return jsonify({"error": "Username is required"}), 400
    if skill_level is None or not isinstance(skill_level, int) or not (0 <= skill_level <= 10):
        return jsonify({"error": "Skill level must be an integer from 0 to 10"}), 400
    if not gender:
        return jsonify({"error": "Gender is required"}), 400

    existing_email = User.query.filter_by(email=email).first()
    if existing_email and existing_email.id != user_id:
        return jsonify({"error": "Email already in use"}), 400

    existing_username = User.query.filter_by(username=username).first()
    if existing_username and existing_username.id != user_id:
        return jsonify({"error": "Username already taken"}), 400

    user.email = email
    user.full_name = full_name
    user.username = username
    user.skill_level = skill_level
    user.gender = gender
    user.updated_at = datetime.now(timezone.utc)
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
