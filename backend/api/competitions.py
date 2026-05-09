from __future__ import annotations

import json
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request, session

from ..auth import login_required, moderator_or_admin_required
from ..extensions import db
from ..models import (
    AuditCompetitionEvent,
    Competition,
    CompetitionMatch,
    CompetitionPlayer,
    User,
)

competitions_bp = Blueprint("competitions", __name__)

_NEXT_STATUS: dict[str, str] = {
    "draft": "published",
    "published": "draw",
    "draw": "match",
    "match": "finished",
}


def _current_user() -> User:
    return db.session.get(User, session["user_id"])


def _can_manage(user: User) -> bool:
    return user.is_admin or user.is_moderator


def _audit(
    competition_id: int, user_id: int, action: str, detail: dict | None = None
) -> None:
    db.session.add(
        AuditCompetitionEvent(
            competition_id=competition_id,
            user_id=user_id,
            action=action,
            detail=json.dumps(detail) if detail else None,
        )
    )


# ---------------------------------------------------------------------------
# Competitions CRUD
# ---------------------------------------------------------------------------


@competitions_bp.get("/")
@login_required
def list_competitions():
    user = _current_user()
    q = Competition.query
    if not _can_manage(user):
        q = q.filter(Competition.status != "draft")
    competitions = q.order_by(Competition.created_at.desc()).all()
    result = []
    for c in competitions:
        d = c.to_dict()
        d["player_count"] = CompetitionPlayer.query.filter_by(
            competition_id=c.id, status="player"
        ).count()
        d["candidate_count"] = CompetitionPlayer.query.filter_by(
            competition_id=c.id, status="candidate"
        ).count()
        result.append(d)
    return jsonify(result), 200


@competitions_bp.post("/")
@moderator_or_admin_required
def create_competition():
    user = _current_user()
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400

    event_type = data.get("event_type", "singles")
    if event_type not in ("singles", "doubles"):
        return jsonify({"error": "event_type must be 'singles' or 'doubles'"}), 400

    comp = Competition(
        name=name,
        description=(data.get("description") or "").strip() or None,
        event_type=event_type,
        status="draft",
    )
    db.session.add(comp)
    db.session.flush()
    _audit(comp.id, user.id, "competition_created", {"name": name, "event_type": event_type})
    db.session.commit()
    return jsonify(comp.to_dict()), 201


@competitions_bp.get("/<int:competition_id>")
@login_required
def get_competition(competition_id: int):
    user = _current_user()
    comp = db.session.get(Competition, competition_id)
    if not comp or (comp.status == "draft" and not _can_manage(user)):
        return jsonify({"error": "Competition not found"}), 404
    return jsonify(comp.to_dict()), 200


@competitions_bp.put("/<int:competition_id>")
@moderator_or_admin_required
def update_competition(competition_id: int):
    user = _current_user()
    comp = db.session.get(Competition, competition_id)
    if not comp:
        return jsonify({"error": "Competition not found"}), 404

    data = request.get_json(silent=True) or {}
    changed: dict = {}

    if "name" in data:
        name = (data["name"] or "").strip()
        if not name:
            return jsonify({"error": "name cannot be empty"}), 400
        comp.name = name
        changed["name"] = name

    if "description" in data:
        comp.description = (data["description"] or "").strip() or None
        changed["description"] = comp.description

    if "event_type" in data:
        if comp.status != "draft":
            return jsonify({"error": "event_type can only be changed in draft status"}), 409
        et = data["event_type"]
        if et not in ("singles", "doubles"):
            return jsonify({"error": "event_type must be 'singles' or 'doubles'"}), 400
        comp.event_type = et
        changed["event_type"] = et

    comp.updated_at = datetime.now(timezone.utc)
    if changed:
        _audit(comp.id, user.id, "competition_updated", changed)
    db.session.commit()
    return jsonify(comp.to_dict()), 200


# ---------------------------------------------------------------------------
# Lifecycle transitions
# ---------------------------------------------------------------------------


@competitions_bp.post("/<int:competition_id>/transition")
@moderator_or_admin_required
def transition_competition(competition_id: int):
    user = _current_user()
    comp = db.session.get(Competition, competition_id)
    if not comp:
        return jsonify({"error": "Competition not found"}), 404

    data = request.get_json(silent=True) or {}
    requested = data.get("status", "")
    expected = _NEXT_STATUS.get(comp.status)
    if requested != expected:
        return jsonify(
            {
                "error": (
                    f"Cannot transition from '{comp.status}' to '{requested}'. "
                    f"Expected next state: '{expected}'."
                )
            }
        ), 409

    # Guards per target state
    if requested == "draw":
        player_count = CompetitionPlayer.query.filter_by(
            competition_id=comp.id, status="player"
        ).count()
        if player_count < 2:
            return jsonify(
                {
                    "error": (
                        f"Need at least 2 confirmed players to start draw "
                        f"(currently {player_count})."
                    )
                }
            ), 409

    elif requested == "match":
        match_count = CompetitionMatch.query.filter_by(competition_id=comp.id).count()
        if match_count == 0:
            return jsonify(
                {"error": "At least 1 match must be created before starting the match phase."}
            ), 409

    elif requested == "finished":
        unscored = CompetitionMatch.query.filter_by(competition_id=comp.id).filter(
            db.or_(
                CompetitionMatch.score_a.is_(None),
                CompetitionMatch.score_b.is_(None),
            )
        ).count()
        if unscored > 0:
            return jsonify(
                {
                    "error": (
                        f"{unscored} match(es) still have no score. "
                        "All matches must be scored before finishing."
                    )
                }
            ), 409

    old_status = comp.status
    comp.status = requested
    comp.updated_at = datetime.now(timezone.utc)
    _audit(comp.id, user.id, "state_transitioned", {"from": old_status, "to": requested})
    db.session.commit()
    return jsonify(comp.to_dict()), 200


# ---------------------------------------------------------------------------
# Players
# ---------------------------------------------------------------------------


@competitions_bp.get("/<int:competition_id>/players")
@login_required
def list_players(competition_id: int):
    user = _current_user()
    comp = db.session.get(Competition, competition_id)
    if not comp or (comp.status == "draft" and not _can_manage(user)):
        return jsonify({"error": "Competition not found"}), 404
    players = CompetitionPlayer.query.filter_by(competition_id=comp.id).all()
    return jsonify([p.to_dict() for p in players]), 200


@competitions_bp.post("/<int:competition_id>/apply")
@login_required
def apply_to_competition(competition_id: int):
    user = _current_user()
    comp = db.session.get(Competition, competition_id)
    if not comp:
        return jsonify({"error": "Competition not found"}), 404
    if comp.status != "published":
        return jsonify(
            {"error": "Applications are only accepted when the competition is published."}
        ), 409

    existing = CompetitionPlayer.query.filter_by(
        competition_id=comp.id, user_id=user.id
    ).first()
    if existing:
        return jsonify({"error": "Already applied to this competition."}), 409

    cp = CompetitionPlayer(competition_id=comp.id, user_id=user.id, status="candidate")
    db.session.add(cp)
    db.session.commit()
    return jsonify(cp.to_dict()), 201


@competitions_bp.delete("/<int:competition_id>/apply")
@login_required
def withdraw_from_competition(competition_id: int):
    user = _current_user()
    comp = db.session.get(Competition, competition_id)
    if not comp:
        return jsonify({"error": "Competition not found"}), 404
    if comp.status != "published":
        return jsonify(
            {"error": "Withdrawals are only allowed when the competition is published."}
        ), 409

    cp = CompetitionPlayer.query.filter_by(
        competition_id=comp.id, user_id=user.id, status="candidate"
    ).first()
    if not cp:
        return jsonify({"error": "No active application found."}), 404

    db.session.delete(cp)
    db.session.commit()
    return "", 204


@competitions_bp.patch("/<int:competition_id>/players/<int:player_id>")
@moderator_or_admin_required
def update_player_status(competition_id: int, player_id: int):
    user = _current_user()
    comp = db.session.get(Competition, competition_id)
    if not comp:
        return jsonify({"error": "Competition not found"}), 404

    cp = CompetitionPlayer.query.filter_by(
        id=player_id, competition_id=comp.id
    ).first()
    if not cp:
        return jsonify({"error": "Player not found"}), 404

    data = request.get_json(silent=True) or {}
    new_status = data.get("status")
    if new_status not in ("candidate", "player"):
        return jsonify({"error": "status must be 'candidate' or 'player'"}), 400

    cp.status = new_status
    _audit(
        comp.id,
        user.id,
        "player_status_changed",
        {"player_id": player_id, "user_id": cp.user_id, "status": new_status},
    )
    db.session.commit()
    return jsonify(cp.to_dict()), 200


@competitions_bp.delete("/<int:competition_id>/players/<int:player_id>")
@moderator_or_admin_required
def remove_player(competition_id: int, player_id: int):
    user = _current_user()
    comp = db.session.get(Competition, competition_id)
    if not comp:
        return jsonify({"error": "Competition not found"}), 404

    cp = CompetitionPlayer.query.filter_by(
        id=player_id, competition_id=comp.id
    ).first()
    if not cp:
        return jsonify({"error": "Player not found"}), 404

    _audit(
        comp.id,
        user.id,
        "player_removed",
        {"player_id": player_id, "user_id": cp.user_id},
    )
    db.session.delete(cp)
    db.session.commit()
    return "", 204


# ---------------------------------------------------------------------------
# Matches
# ---------------------------------------------------------------------------


@competitions_bp.get("/<int:competition_id>/matches")
@login_required
def list_matches(competition_id: int):
    user = _current_user()
    comp = db.session.get(Competition, competition_id)
    if not comp or (comp.status == "draft" and not _can_manage(user)):
        return jsonify({"error": "Competition not found"}), 404
    matches = CompetitionMatch.query.filter_by(competition_id=comp.id).all()
    return jsonify([m.to_dict() for m in matches]), 200


@competitions_bp.post("/<int:competition_id>/matches")
@moderator_or_admin_required
def create_match(competition_id: int):
    user = _current_user()
    comp = db.session.get(Competition, competition_id)
    if not comp:
        return jsonify({"error": "Competition not found"}), 404
    if comp.status != "draw":
        return jsonify({"error": "Matches can only be created during the draw phase."}), 409

    data = request.get_json(silent=True) or {}
    player_a_id = data.get("player_a_id")
    player_b_id = data.get("player_b_id")

    if not player_a_id or not player_b_id:
        return jsonify({"error": "player_a_id and player_b_id are required"}), 400
    if player_a_id == player_b_id:
        return jsonify({"error": "A player cannot match against themselves."}), 400

    pa = CompetitionPlayer.query.filter_by(
        id=player_a_id, competition_id=comp.id, status="player"
    ).first()
    pb = CompetitionPlayer.query.filter_by(
        id=player_b_id, competition_id=comp.id, status="player"
    ).first()

    if not pa:
        return jsonify({"error": "Player A not found or not confirmed in this competition."}), 404
    if not pb:
        return jsonify({"error": "Player B not found or not confirmed in this competition."}), 404

    match = CompetitionMatch(
        competition_id=comp.id,
        player_a_id=player_a_id,
        player_b_id=player_b_id,
    )
    db.session.add(match)
    db.session.flush()
    _audit(
        comp.id,
        user.id,
        "match_created",
        {"match_id": match.id, "player_a_id": player_a_id, "player_b_id": player_b_id},
    )
    db.session.commit()
    return jsonify(match.to_dict()), 201


@competitions_bp.patch("/<int:competition_id>/matches/<int:match_id>/score")
@login_required
def set_score(competition_id: int, match_id: int):
    user = _current_user()
    comp = db.session.get(Competition, competition_id)
    if not comp:
        return jsonify({"error": "Competition not found"}), 404
    if comp.status != "match":
        return jsonify({"error": "Scores can only be entered during the match phase."}), 409

    match = CompetitionMatch.query.filter_by(
        id=match_id, competition_id=comp.id
    ).first()
    if not match:
        return jsonify({"error": "Match not found"}), 404

    is_manager = _can_manage(user)
    if not is_manager:
        pa = db.session.get(CompetitionPlayer, match.player_a_id)
        pb = db.session.get(CompetitionPlayer, match.player_b_id)
        allowed = {p.user_id for p in (pa, pb) if p}
        if user.id not in allowed:
            return jsonify(
                {"error": "You can only score matches you are participating in."}
            ), 403

    data = request.get_json(silent=True) or {}
    score_a = data.get("score_a")
    score_b = data.get("score_b")

    if score_a is None or score_b is None:
        return jsonify({"error": "score_a and score_b are required"}), 400
    if isinstance(score_a, bool) or not isinstance(score_a, int):
        return jsonify({"error": "score_a must be an integer"}), 400
    if isinstance(score_b, bool) or not isinstance(score_b, int):
        return jsonify({"error": "score_b must be an integer"}), 400
    if score_a < 0 or score_b < 0:
        return jsonify({"error": "Scores must be non-negative"}), 400

    match.score_a = score_a
    match.score_b = score_b
    if is_manager:
        _audit(
            comp.id,
            user.id,
            "match_scored",
            {"match_id": match_id, "score_a": score_a, "score_b": score_b},
        )
    db.session.commit()
    return jsonify(match.to_dict()), 200
