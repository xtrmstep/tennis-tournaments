from __future__ import annotations

import functools

from flask import Blueprint, jsonify, request, session

from .extensions import db
from .models import User

auth_bp = Blueprint("auth", __name__)


def login_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)

    return decorated


@auth_bp.post("/signup")
def signup():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not email or "@" not in email:
        return jsonify({"error": "Valid email is required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 400

    user = User(email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    session["user_id"] = user.id
    return jsonify(user.to_dict()), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401

    session["user_id"] = user.id
    return jsonify(user.to_dict()), 200


@auth_bp.post("/logout")
def logout():
    session.clear()
    return jsonify({"message": "Logged out"}), 200


@auth_bp.get("/me")
@login_required
def me():
    user = db.session.get(User, session["user_id"])
    if not user:
        session.clear()
        return jsonify({"error": "User not found"}), 401
    return jsonify(user.to_dict()), 200


@auth_bp.put("/profile")
@login_required
def update_profile():
    user = db.session.get(User, session["user_id"])
    if not user:
        session.clear()
        return jsonify({"error": "User not found"}), 401

    data = request.get_json(silent=True) or {}
    full_name = (data.get("full_name") or "").strip()
    username = (data.get("username") or "").strip()
    skill_level = data.get("skill_level")
    gender = (data.get("gender") or "").strip()

    if not full_name:
        return jsonify({"error": "Full name is required"}), 400
    if not username:
        return jsonify({"error": "Username is required"}), 400
    if skill_level is None or not isinstance(skill_level, int) or not (0 <= skill_level <= 10):
        return jsonify({"error": "Skill level must be an integer from 0 to 10"}), 400
    if not gender:
        return jsonify({"error": "Gender is required"}), 400

    existing = User.query.filter_by(username=username).first()
    if existing and existing.id != user.id:
        return jsonify({"error": "Username already taken"}), 400

    user.full_name = full_name
    user.username = username
    user.skill_level = skill_level
    user.gender = gender
    db.session.commit()

    return jsonify(user.to_dict()), 200
