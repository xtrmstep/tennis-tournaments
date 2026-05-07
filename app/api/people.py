from __future__ import annotations

import os

from flask import Blueprint, current_app, jsonify, request, send_file

from ..auth import login_required
from ..extensions import db
from ..models import Person

people_bp = Blueprint("people", __name__)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif"}

# Map normalised extension to a safe, fixed suffix used when saving photos.
_EXT_MAP = {".jpg": ".jpg", ".jpeg": ".jpg", ".png": ".png", ".gif": ".gif"}


def _allowed_photo(filename: str) -> bool:
    _, ext = os.path.splitext(filename.lower())
    return ext in ALLOWED_EXTENSIONS


@people_bp.get("/")
@login_required
def list_people():
    people = Person.query.order_by(Person.created_at).all()
    return jsonify([p.to_dict() for p in people]), 200


@people_bp.post("/")
@login_required
def create_person():
    name = request.form.get("name", "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400

    skill = request.form.get("skill", "").strip() or None

    person = Person(name=name, skill=skill)
    db.session.add(person)
    db.session.flush()  # get id before commit

    photo = request.files.get("photo")
    if photo and photo.filename:
        if not _allowed_photo(photo.filename):
            db.session.rollback()
            return jsonify({"error": "Photo must be jpg, jpeg, png, or gif"}), 400

        _, raw_ext = os.path.splitext(photo.filename.lower())
        # Use a controlled suffix from the allow-list — never trust raw user input in paths.
        safe_ext = _EXT_MAP[raw_ext]
        uploads_dir = os.path.join(current_app.instance_path, "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        save_path = os.path.join(uploads_dir, f"{person.id}{safe_ext}")
        photo.save(save_path)
        person.photo_path = save_path

    db.session.commit()
    return jsonify(person.to_dict()), 201


@people_bp.get("/<int:person_id>")
@login_required
def get_person(person_id: int):
    person = db.session.get(Person, person_id)
    if not person:
        return jsonify({"error": "Person not found"}), 404
    return jsonify(person.to_dict()), 200


@people_bp.put("/<int:person_id>/rating")
@login_required
def update_rating(person_id: int):
    person = db.session.get(Person, person_id)
    if not person:
        return jsonify({"error": "Person not found"}), 404

    data = request.get_json(silent=True) or {}
    raw = data.get("rating")

    if raw is None:
        return jsonify({"error": "rating is required"}), 400

    if not isinstance(raw, int) or isinstance(raw, bool):
        # bool subclasses int in Python, so exclude it explicitly.
        return jsonify({"error": "rating must be an integer 1-10"}), 400

    if raw < 1 or raw > 10:
        return jsonify({"error": "rating must be between 1 and 10"}), 400

    person.rating = raw
    db.session.commit()
    return jsonify(person.to_dict()), 200


@people_bp.get("/<int:person_id>/photo")
@login_required
def get_photo(person_id: int):
    person = db.session.get(Person, person_id)
    if not person or not person.photo_path:
        return jsonify({"error": "Photo not found"}), 404
    if not os.path.exists(person.photo_path):
        return jsonify({"error": "Photo file missing"}), 404
    return send_file(person.photo_path), 200
