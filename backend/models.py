from __future__ import annotations

import json
from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


class User(db.Model):
    __tablename__ = "users"
    id: int = db.Column(db.Integer, primary_key=True)
    email: str = db.Column(db.String(200), unique=True, nullable=False)
    password_hash: str = db.Column(db.String(256), nullable=False)
    full_name: str | None = db.Column(db.String(200), nullable=True)
    username: str | None = db.Column(db.String(100), unique=True, nullable=True)
    skill_level: int | None = db.Column(db.Integer, nullable=True)  # 0-10
    gender: str | None = db.Column(db.String(50), nullable=True)
    is_active: bool = db.Column(db.Boolean, nullable=False, default=True)
    is_admin: bool = db.Column(db.Boolean, nullable=False, default=False)
    is_moderator: bool = db.Column(db.Boolean, nullable=False, default=False)
    created_at: datetime = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime | None = db.Column(db.DateTime, nullable=True)

    @property
    def profile_complete(self) -> bool:
        return all(
            f is not None
            for f in (self.full_name, self.username, self.skill_level, self.gender)
        )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "username": self.username,
            "skill_level": self.skill_level,
            "gender": self.gender,
            "profile_complete": self.profile_complete,
            "is_active": self.is_active,
            "is_admin": self.is_admin,
            "is_moderator": self.is_moderator,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Person(db.Model):
    __tablename__ = "people"
    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(200), nullable=False)
    photo_path: str | None = db.Column(db.String(500), nullable=True)
    skill: str | None = db.Column(db.String(200), nullable=True)
    rating: int | None = db.Column(db.Integer, nullable=True)  # 1-10
    created_at: datetime = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "photo_url": f"/api/people/{self.id}/photo" if self.photo_path else None,
            "skill": self.skill,
            "rating": self.rating,
        }


class SortResult(db.Model):
    __tablename__ = "sort_results"
    id: int = db.Column(db.Integer, primary_key=True)
    mode: str = db.Column(db.String(20), nullable=False)  # 'singles' or 'doubles'
    items_json: str = db.Column(db.Text, nullable=False)
    generated_at: datetime = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> dict:
        return {
            "mode": self.mode,
            "generated_at": self.generated_at.isoformat(),
            "items": json.loads(self.items_json),
        }


class AuditAuthEvent(db.Model):
    __tablename__ = "audit_auth_events"
    id: int = db.Column(db.Integer, primary_key=True)
    email: str = db.Column(db.String(200), nullable=False)
    event_type: str = db.Column(db.String(20), nullable=False)  # 'login' or 'logout'
    success: bool = db.Column(db.Boolean, nullable=False)
    attempted_at: datetime = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    __table_args__ = (
        db.Index("ix_audit_auth_events_email_at", "email", "attempted_at"),
    )


class Competition(db.Model):
    __tablename__ = "competitions"
    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(200), nullable=False)
    description: str | None = db.Column(db.Text, nullable=True)
    event_type: str = db.Column(db.String(20), nullable=False, default="singles")  # 'singles' or 'doubles'
    status: str = db.Column(db.String(20), nullable=False, default="draft")  # draft/published/grouping/draw/match/finished
    created_at: datetime = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime | None = db.Column(db.DateTime, nullable=True)

    players = db.relationship(
        "CompetitionPlayer", back_populates="competition", cascade="all, delete-orphan"
    )
    pairs = db.relationship(
        "CompetitionPair", back_populates="competition", cascade="all, delete-orphan"
    )
    matches = db.relationship(
        "CompetitionMatch", back_populates="competition", cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "event_type": self.event_type,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class CompetitionPlayer(db.Model):
    __tablename__ = "competition_players"
    id: int = db.Column(db.Integer, primary_key=True)
    competition_id: int = db.Column(
        db.Integer, db.ForeignKey("competitions.id"), nullable=False
    )
    user_id: int = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status: str = db.Column(db.String(20), nullable=False, default="candidate")  # 'candidate' or 'player'
    joined_at: datetime = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    competition = db.relationship("Competition", back_populates="players")
    user = db.relationship("User")

    __table_args__ = (
        db.UniqueConstraint(
            "competition_id", "user_id", name="uq_competition_players_comp_user"
        ),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "competition_id": self.competition_id,
            "user_id": self.user_id,
            "status": self.status,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "username": self.user.username if self.user else None,
            "full_name": self.user.full_name if self.user else None,
        }


class CompetitionMatch(db.Model):
    __tablename__ = "competition_matches"
    id: int = db.Column(db.Integer, primary_key=True)
    competition_id: int = db.Column(
        db.Integer, db.ForeignKey("competitions.id"), nullable=False
    )
    player_a_id: int = db.Column(
        db.Integer, db.ForeignKey("competition_players.id"), nullable=False
    )
    player_b_id: int = db.Column(
        db.Integer, db.ForeignKey("competition_players.id"), nullable=False
    )
    score_a: int | None = db.Column(db.Integer, nullable=True)
    score_b: int | None = db.Column(db.Integer, nullable=True)
    created_at: datetime = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    competition = db.relationship("Competition", back_populates="matches")
    player_a = db.relationship("CompetitionPlayer", foreign_keys=[player_a_id])
    player_b = db.relationship("CompetitionPlayer", foreign_keys=[player_b_id])

    def to_dict(self) -> dict:
        pa = self.player_a
        pb = self.player_b
        return {
            "id": self.id,
            "competition_id": self.competition_id,
            "player_a_id": self.player_a_id,
            "player_b_id": self.player_b_id,
            "player_a_user_id": pa.user_id if pa else None,
            "player_b_user_id": pb.user_id if pb else None,
            "player_a_name": (
                (pa.user.full_name or pa.user.username) if pa and pa.user else f"Player {self.player_a_id}"
            ),
            "player_b_name": (
                (pb.user.full_name or pb.user.username) if pb and pb.user else f"Player {self.player_b_id}"
            ),
            "score_a": self.score_a,
            "score_b": self.score_b,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CompetitionPair(db.Model):
    __tablename__ = "competition_pairs"
    id: int = db.Column(db.Integer, primary_key=True)
    competition_id: int = db.Column(
        db.Integer, db.ForeignKey("competitions.id"), nullable=False
    )
    player_a_id: int = db.Column(
        db.Integer, db.ForeignKey("competition_players.id"), nullable=False
    )
    player_b_id: int = db.Column(
        db.Integer, db.ForeignKey("competition_players.id"), nullable=False
    )
    created_at: datetime = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    competition = db.relationship("Competition", back_populates="pairs")
    player_a = db.relationship("CompetitionPlayer", foreign_keys=[player_a_id])
    player_b = db.relationship("CompetitionPlayer", foreign_keys=[player_b_id])

    __table_args__ = (
        db.UniqueConstraint(
            "competition_id", "player_a_id", name="uq_competition_pair_a"
        ),
        db.UniqueConstraint(
            "competition_id", "player_b_id", name="uq_competition_pair_b"
        ),
    )

    def to_dict(self) -> dict:
        pa = self.player_a
        pb = self.player_b
        return {
            "id": self.id,
            "competition_id": self.competition_id,
            "player_a_id": self.player_a_id,
            "player_b_id": self.player_b_id,
            "player_a_user_id": pa.user_id if pa else None,
            "player_b_user_id": pb.user_id if pb else None,
            "player_a_name": (
                (pa.user.full_name or pa.user.username) if pa and pa.user else f"Player {self.player_a_id}"
            ),
            "player_b_name": (
                (pb.user.full_name or pb.user.username) if pb and pb.user else f"Player {self.player_b_id}"
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AuditCompetitionEvent(db.Model):
    __tablename__ = "audit_competition_events"
    id: int = db.Column(db.Integer, primary_key=True)
    competition_id: int = db.Column(
        db.Integer, db.ForeignKey("competitions.id"), nullable=False
    )
    user_id: int = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    action: str = db.Column(db.String(50), nullable=False)
    detail: str | None = db.Column(db.Text, nullable=True)
    created_at: datetime = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        db.Index("ix_audit_competition_events_comp", "competition_id"),
    )
