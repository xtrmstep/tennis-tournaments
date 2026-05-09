from __future__ import annotations

import functools
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request, session

from .extensions import db
from .models import AuditAuthEvent, User

auth_bp = Blueprint("auth", __name__)

_BURST_LIMIT = 10
_BURST_WINDOW_SECONDS = 60
_BURST_SUSPENSION_HOURS = 24
_BRUTE_WINDOW_SECONDS = 600
_BRUTE_SUSPENSION_HOURS = 1


def _record_auth_event(email: str, event_type: str, success: bool) -> None:
    db.session.add(AuditAuthEvent(email=email, event_type=event_type, success=success))
    db.session.commit()


def _check_rate_limit(email: str) -> tuple[bool, str]:
    now = datetime.now(timezone.utc)

    # Burst rule: >= 10 login events within last 24 h whose span is <= 60 s
    recent_any = (
        AuditAuthEvent.query
        .filter(
            AuditAuthEvent.email == email,
            AuditAuthEvent.event_type == "login",
            AuditAuthEvent.attempted_at >= now - timedelta(hours=_BURST_SUSPENSION_HOURS),
        )
        .order_by(AuditAuthEvent.attempted_at.desc())
        .limit(_BURST_LIMIT)
        .all()
    )
    if len(recent_any) >= _BURST_LIMIT:
        span = (recent_any[0].attempted_at - recent_any[-1].attempted_at).total_seconds()
        if span <= _BURST_WINDOW_SECONDS:
            return True, "Too many requests. Account suspended for 24 hours."

    # Brute-force rule: >= 10 failed login events within last 1 h whose span is <= 10 min
    recent_failed = (
        AuditAuthEvent.query
        .filter(
            AuditAuthEvent.email == email,
            AuditAuthEvent.event_type == "login",
            AuditAuthEvent.success.is_(False),
            AuditAuthEvent.attempted_at >= now - timedelta(hours=_BRUTE_SUSPENSION_HOURS),
        )
        .order_by(AuditAuthEvent.attempted_at.desc())
        .limit(_BURST_LIMIT)
        .all()
    )
    if len(recent_failed) >= _BURST_LIMIT:
        span = (recent_failed[0].attempted_at - recent_failed[-1].attempted_at).total_seconds()
        if span <= _BRUTE_WINDOW_SECONDS:
            return True, "Too many failed attempts. Account suspended for 1 hour."

    return False, ""


def login_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Authentication required"}), 401
        user = db.session.get(User, session["user_id"])
        if not user or not user.is_admin:
            return jsonify({"error": "Admin access required"}), 403
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

    blocked, block_msg = _check_rate_limit(email)
    if blocked:
        return jsonify({"error": block_msg}), 429

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        _record_auth_event(email, "login", False)
        return jsonify({"error": "Invalid credentials"}), 401
    if not user.is_active:
        _record_auth_event(email, "login", False)
        return jsonify({"error": "Account is disabled"}), 403

    _record_auth_event(email, "login", True)
    session["user_id"] = user.id
    return jsonify(user.to_dict()), 200


@auth_bp.post("/logout")
def logout():
    user_id = session.get("user_id")
    if user_id:
        user = db.session.get(User, user_id)
        if user:
            _record_auth_event(user.email, "logout", True)
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
    user.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify(user.to_dict()), 200
