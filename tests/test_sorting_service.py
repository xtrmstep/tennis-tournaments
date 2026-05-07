from __future__ import annotations

import pytest

from app.services.sorting_service import run_sorting


class FakePerson:
    """Minimal stand-in for app.models.Person (no DB needed)."""

    def __init__(self, id: int, name: str, rating: int | None = None, skill: str | None = None):
        self.id = id
        self.name = name
        self.rating = rating
        self.skill = skill
        self.photo_path = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "photo_url": None,
            "skill": self.skill,
            "rating": self.rating,
        }


# ---------------------------------------------------------------------------
# Singles
# ---------------------------------------------------------------------------

def test_singles_sorted_by_rating_descending():
    people = [
        FakePerson(1, "Alice", rating=3),
        FakePerson(2, "Bob", rating=7),
        FakePerson(3, "Carol", rating=5),
    ]
    result = run_sorting(people, "singles")
    ratings = [r["rating"] for r in result]
    assert ratings == sorted(ratings, reverse=True)


def test_singles_none_rating_sorts_last():
    people = [
        FakePerson(1, "Alice", rating=None),
        FakePerson(2, "Bob", rating=4),
        FakePerson(3, "Carol", rating=9),
    ]
    result = run_sorting(people, "singles")
    assert result[-1]["rating"] is None
    assert result[0]["rating"] == 9


def test_singles_all_none_ratings():
    people = [FakePerson(i, f"P{i}", rating=None) for i in range(4)]
    result = run_sorting(people, "singles")
    assert len(result) == 4


def test_singles_empty():
    result = run_sorting([], "singles")
    assert result == []


# ---------------------------------------------------------------------------
# Doubles
# ---------------------------------------------------------------------------

def test_doubles_returns_teams():
    people = [FakePerson(i, f"P{i}", rating=i + 1) for i in range(4)]
    result = run_sorting(people, "doubles")
    assert len(result) == 2
    for team in result:
        assert "team_id" in team
        assert "player1" in team
        assert "player2" in team
        assert "pair_strength" in team


def test_doubles_pair_strength_is_sum_of_skill_percents():
    people = [FakePerson(i, f"P{i}", rating=i + 1) for i in range(4)]
    result = run_sorting(people, "doubles")
    for team in result:
        p1_rating = team["player1"]["rating"] or 5
        p2_rating = team["player2"]["rating"] or 5
        expected = p1_rating * 10 + p2_rating * 10
        assert team["pair_strength"] == expected


def test_doubles_requires_even_count():
    people = [FakePerson(i, f"P{i}", rating=5) for i in range(3)]
    with pytest.raises(ValueError, match="even"):
        run_sorting(people, "doubles")


def test_doubles_requires_at_least_two():
    people = [FakePerson(1, "Solo", rating=5)]
    with pytest.raises(ValueError):
        run_sorting(people, "doubles")


def test_doubles_empty_raises():
    with pytest.raises(ValueError):
        run_sorting([], "doubles")


def test_doubles_with_none_rating_defaults_to_50_percent():
    people = [
        FakePerson(1, "Alice", rating=None),
        FakePerson(2, "Bob", rating=None),
    ]
    result = run_sorting(people, "doubles")
    assert len(result) == 1
    assert result[0]["pair_strength"] == 100  # 5*10 + 5*10


# ---------------------------------------------------------------------------
# Invalid mode
# ---------------------------------------------------------------------------

def test_invalid_mode_raises_value_error():
    with pytest.raises(ValueError, match="Invalid sorting mode"):
        run_sorting([], "triples")
