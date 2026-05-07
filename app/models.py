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
    created_at: datetime = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


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
