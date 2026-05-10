from __future__ import annotations

from flask import Blueprint, jsonify

from ..auth import login_required
from ..models import User

users_bp = Blueprint("users", __name__)


def _public_dict(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "skill_level": user.skill_level,
        "gender": user.gender,
        "photo_url": None,  # reserved for future avatar support
    }


@users_bp.get("/")
@login_required
def list_users():
    users = (
        User.query
        .filter(User.is_active.is_(True), User.full_name.isnot(None))
        .order_by(User.full_name)
        .all()
    )
    return jsonify([_public_dict(u) for u in users]), 200
