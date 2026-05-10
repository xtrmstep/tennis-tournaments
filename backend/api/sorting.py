from __future__ import annotations

import json

from flask import Blueprint, current_app, jsonify, request

from ..auth import login_required
from ..extensions import db
from ..models import Person, SortResult
from ..services.sorting_service import run_sorting

sorting_bp = Blueprint("sorting", __name__)


@sorting_bp.post("/run")
@login_required
def run_sort():
    data = request.get_json(silent=True) or {}
    mode = data.get("mode", "")
    seed = data.get("seed")

    if mode not in ("singles", "doubles"):
        return jsonify({"error": "mode must be 'singles' or 'doubles'"}), 400

    people = Person.query.order_by(Person.created_at).all()

    try:
        items = run_sorting(people, mode, seed=seed)
    except ValueError as exc:
        # Break the user-input → response data-flow chain by constructing a
        # controlled error string instead of forwarding str(exc) directly.
        current_app.logger.debug("Sorting validation error: %s", exc)
        people_count = len(people)
        error_msg = (
            f"Cannot run {mode} sorting with {people_count} "
            f"{'person' if people_count == 1 else 'people'}. "
            "Doubles requires an even count of at least 2."
        )
        return jsonify({"error": error_msg}), 400

    # Replace all previous results
    SortResult.query.delete()
    result = SortResult(mode=mode, items_json=json.dumps(items))
    db.session.add(result)
    db.session.commit()

    return jsonify(result.to_dict()), 200


@sorting_bp.get("/result")
@login_required
def get_result():
    result = SortResult.query.order_by(SortResult.generated_at.desc()).first()
    if not result:
        return jsonify({"error": "No sorting result found"}), 404
    return jsonify(result.to_dict()), 200
