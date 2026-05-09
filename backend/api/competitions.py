from __future__ import annotations

import json
import string
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request, session

from bracket import generate_bracket
from models import Participant, PairingMode, Team
from pairing import generate_teams
from scheduling import assign_courts
from ..auth import login_required, moderator_or_admin_required
from ..extensions import db
from ..models import (
    AuditCompetitionEvent,
    Competition,
    CompetitionDraw,
    CompetitionMatch,
    CompetitionPair,
    CompetitionPlayer,
    User,
)

competitions_bp = Blueprint("competitions", __name__)

# Doubles lifecycle: draft → published → grouping → draw → match → finished
# Singles lifecycle: draft → published → draw → match → finished
_SINGLES_NEXT: dict[str, str] = {
    "draft": "published",
    "published": "draw",
    "draw": "match",
    "match": "finished",
}
_DOUBLES_NEXT: dict[str, str] = {
    "draft": "published",
    "published": "grouping",
    "grouping": "draw",
    "draw": "match",
    "match": "finished",
}


def _next_status(comp: Competition) -> str | None:
    mapping = _DOUBLES_NEXT if comp.event_type == "doubles" else _SINGLES_NEXT
    return mapping.get(comp.status)


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
    expected = _next_status(comp)
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
    if requested == "grouping":
        # Only doubles competitions reach this state
        player_count = CompetitionPlayer.query.filter_by(
            competition_id=comp.id, status="player"
        ).count()
        if player_count < 2:
            return jsonify(
                {
                    "error": (
                        f"Need at least 2 confirmed players to start grouping "
                        f"(currently {player_count})."
                    )
                }
            ), 409

    elif requested == "draw":
        confirmed_players = CompetitionPlayer.query.filter_by(
            competition_id=comp.id, status="player"
        ).all()
        player_count = len(confirmed_players)
        if player_count < 2:
            return jsonify(
                {
                    "error": (
                        f"Need at least 2 confirmed players to start draw "
                        f"(currently {player_count})."
                    )
                }
            ), 409
        if comp.event_type == "doubles":
            existing_pairs = CompetitionPair.query.filter_by(competition_id=comp.id).all()
            paired_ids: set[int] = {
                pid
                for pair in existing_pairs
                for pid in (pair.player_a_id, pair.player_b_id)
            }
            unpaired = [cp for cp in confirmed_players if cp.id not in paired_ids]
            if len(unpaired) % 2 != 0:
                return jsonify(
                    {
                        "error": (
                            f"{len(unpaired)} confirmed player(s) are unpaired and cannot form "
                            "complete pairs. Manually pair or adjust confirmed players first."
                        )
                    }
                ), 409
            if unpaired:
                participants = [
                    Participant(
                        id=str(cp.id),
                        name=(cp.user.full_name or cp.user.username or str(cp.user_id)),
                        gender=(cp.user.gender or "male"),
                        skill_percent=(cp.user.skill_level or 5) * 10,
                    )
                    for cp in unpaired
                ]
                auto_teams = generate_teams(participants, PairingMode.RANDOM)
                pair_offset = len(existing_pairs)
                for idx, team in enumerate(auto_teams):
                    letter = string.ascii_uppercase[(pair_offset + idx) % 26]
                    db.session.add(CompetitionPair(
                        competition_id=comp.id,
                        player_a_id=int(team.player1.id),
                        player_b_id=int(team.player2.id),
                        team_name=f"Team {letter}",
                    ))

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


# ---------------------------------------------------------------------------
# Pairs (doubles grouping stage)
# ---------------------------------------------------------------------------


@competitions_bp.get("/<int:competition_id>/pairs")
@login_required
def list_pairs(competition_id: int):
    user = _current_user()
    comp = db.session.get(Competition, competition_id)
    if not comp or (comp.status == "draft" and not _can_manage(user)):
        return jsonify({"error": "Competition not found"}), 404
    pairs = CompetitionPair.query.filter_by(competition_id=comp.id).all()
    return jsonify([p.to_dict() for p in pairs]), 200


@competitions_bp.post("/<int:competition_id>/pairs")
@login_required
def create_pair(competition_id: int):
    user = _current_user()
    comp = db.session.get(Competition, competition_id)
    if not comp:
        return jsonify({"error": "Competition not found"}), 404
    if comp.event_type != "doubles":
        return jsonify({"error": "Pairs only exist in doubles competitions."}), 409
    if comp.status != "grouping":
        return jsonify({"error": "Pairs can only be created during the grouping phase."}), 409

    data = request.get_json(silent=True) or {}
    player_a_id = data.get("player_a_id")
    player_b_id = data.get("player_b_id")

    if not player_a_id or not player_b_id:
        return jsonify({"error": "player_a_id and player_b_id are required"}), 400
    if player_a_id == player_b_id:
        return jsonify({"error": "A player cannot be paired with themselves."}), 400

    # Non-managers may only create pairs that include their own confirmed entry
    if not _can_manage(user):
        my_entry = CompetitionPlayer.query.filter_by(
            competition_id=comp.id, user_id=user.id, status="player"
        ).first()
        if not my_entry:
            return jsonify({"error": "You must be a confirmed player in this competition."}), 403
        if my_entry.id not in (player_a_id, player_b_id):
            return jsonify({"error": "You can only create pairs that include yourself."}), 403

    team_name = data.get("team_name")
    if team_name is not None:
        team_name = team_name.strip()
        if len(team_name) > 100:
            return jsonify({"error": "team_name must be 100 characters or fewer."}), 400
        if not team_name:
            team_name = None

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

    # Check neither player is already in a pair
    already_paired = CompetitionPair.query.filter_by(competition_id=comp.id).filter(
        db.or_(
            CompetitionPair.player_a_id.in_([player_a_id, player_b_id]),
            CompetitionPair.player_b_id.in_([player_a_id, player_b_id]),
        )
    ).first()
    if already_paired:
        return jsonify({"error": "One or both players are already in a pair."}), 409

    # Auto-generate team name from CLI pattern (Team A, Team B, …) when not supplied
    if team_name is None:
        existing_count = CompetitionPair.query.filter_by(competition_id=comp.id).count()
        letter = string.ascii_uppercase[existing_count % 26]
        team_name = f"Team {letter}"

    pair = CompetitionPair(
        competition_id=comp.id,
        player_a_id=player_a_id,
        player_b_id=player_b_id,
        team_name=team_name,
    )
    db.session.add(pair)
    db.session.flush()
    _audit(
        comp.id,
        user.id,
        "pair_created",
        {"pair_id": pair.id, "player_a_id": player_a_id, "player_b_id": player_b_id},
    )
    db.session.commit()
    return jsonify(pair.to_dict()), 201


@competitions_bp.delete("/<int:competition_id>/pairs/<int:pair_id>")
@moderator_or_admin_required
def delete_pair(competition_id: int, pair_id: int):
    user = _current_user()
    comp = db.session.get(Competition, competition_id)
    if not comp:
        return jsonify({"error": "Competition not found"}), 404
    if comp.status != "grouping":
        return jsonify({"error": "Pairs can only be removed during the grouping phase."}), 409

    pair = CompetitionPair.query.filter_by(id=pair_id, competition_id=comp.id).first()
    if not pair:
        return jsonify({"error": "Pair not found"}), 404

    _audit(
        comp.id,
        user.id,
        "pair_deleted",
        {"pair_id": pair_id},
    )
    db.session.delete(pair)
    db.session.commit()
    return "", 204


# ---------------------------------------------------------------------------
# Draw generation (bracket + court assignment)
# ---------------------------------------------------------------------------

@competitions_bp.post("/<int:competition_id>/draw/generate")
@moderator_or_admin_required
def generate_draw(competition_id: int):
    user = _current_user()
    comp = db.session.get(Competition, competition_id)
    if not comp:
        return jsonify({"error": "Competition not found"}), 404
    if comp.status != "draw":
        return jsonify({"error": "Bracket can only be generated in draw status."}), 409

    data = request.get_json(silent=True) or {}
    num_courts = data.get("num_courts")
    if num_courts is None or not isinstance(num_courts, int) or num_courts < 1:
        return jsonify({"error": "num_courts must be a positive integer"}), 400

    confirmed = (
        CompetitionPlayer.query.filter_by(competition_id=comp.id, status="player")
        .join(CompetitionPlayer.user)
        .all()
    )

    if comp.event_type == "singles":
        if len(confirmed) < 2:
            return jsonify({"error": "Need at least 2 confirmed players to generate a bracket."}), 409
        teams: list[Team] = []
        unit_map: dict[str, dict] = {}
        for idx, cp in enumerate(confirmed):
            tid = string.ascii_uppercase[idx % 26]
            skill = (cp.user.skill_level or 0) * 10
            p = Participant(id=str(cp.id), name="", gender="", skill_percent=skill)
            teams.append(Team(team_id=tid, player1=p, player2=p))
            label = cp.user.full_name or cp.user.username or f"Player {cp.id}"
            unit_map[tid] = {"unit_id": cp.id, "label": label}
    else:
        pairs = CompetitionPair.query.filter_by(competition_id=comp.id).all()
        if len(pairs) < 2:
            return jsonify({"error": "Need at least 2 pairs to generate a bracket."}), 409
        teams = []
        unit_map = {}
        for idx, pair in enumerate(pairs):
            tid = string.ascii_uppercase[idx % 26]
            pa = pair.player_a
            pb = pair.player_b
            skill_a = (pa.user.skill_level or 0) * 10 if pa and pa.user else 0
            skill_b = (pb.user.skill_level or 0) * 10 if pb and pb.user else 0
            p1 = Participant(id=str(pa.id if pa else 0), name="", gender="", skill_percent=skill_a)
            p2 = Participant(id=str(pb.id if pb else 0), name="", gender="", skill_percent=skill_b)
            teams.append(Team(team_id=tid, player1=p1, player2=p2))
            unit_map[tid] = {"unit_id": pair.id, "label": pair.team_name or tid}

    bracket_matches = generate_bracket(teams)
    assign_courts(bracket_matches, num_courts)

    slots = []
    for m in bracket_matches:
        def _resolve(label: str) -> tuple[int | None, str]:
            info = unit_map.get(label)
            if info:
                return info["unit_id"], info["label"]
            return None, label

        uid_a, lbl_a = _resolve(m.team1)
        uid_b, lbl_b = _resolve(m.team2)
        slots.append({
            "match_id": m.match_id,
            "round": m.round_name,
            "court": m.court,
            "time_slot": m.time_slot,
            "label_a": lbl_a,
            "label_b": lbl_b,
            "unit_a_id": uid_a,
            "unit_b_id": uid_b,
        })

    existing = CompetitionDraw.query.filter_by(competition_id=comp.id).first()
    if existing:
        existing.num_courts = num_courts
        existing.bracket_json = json.dumps(slots)
        existing.generated_at = datetime.now(timezone.utc)
        draw = existing
    else:
        draw = CompetitionDraw(
            competition_id=comp.id,
            num_courts=num_courts,
            bracket_json=json.dumps(slots),
        )
        db.session.add(draw)

    _audit(comp.id, user.id, "draw_generated", {"num_courts": num_courts})
    db.session.commit()
    return jsonify(draw.to_dict()), 200


@competitions_bp.get("/<int:competition_id>/draw")
@login_required
def get_draw(competition_id: int):
    comp = db.session.get(Competition, competition_id)
    if not comp:
        return jsonify({"error": "Competition not found"}), 404
    draw = CompetitionDraw.query.filter_by(competition_id=comp.id).first()
    if not draw:
        return jsonify({"error": "No draw generated yet."}), 404
    return jsonify(draw.to_dict()), 200

