from __future__ import annotations

import pytest

from models import Participant, PairingMode
from pairing import generate_teams


def _make(name: str, gender: str, skill: int) -> Participant:
    return Participant(id=f"p_{name}", name=name, gender=gender, skill_percent=skill)


def _males(n: int, start_skill: int = 50) -> list[Participant]:
    return [_make(f"M{i}", "male", start_skill + i * 3) for i in range(n)]


def _females(n: int, start_skill: int = 50) -> list[Participant]:
    return [_make(f"F{i}", "female", start_skill + i * 3) for i in range(n)]


class TestMixedPairing:
    def test_valid_mixed(self) -> None:
        participants = _males(4) + _females(4)
        teams = generate_teams(participants, PairingMode.MIXED, seed=1)
        assert len(teams) == 4
        for t in teams:
            genders = {t.player1.gender, t.player2.gender}
            assert genders == {"male", "female"}

    def test_impossible_mixed_unequal(self) -> None:
        participants = _males(3) + _females(1)
        with pytest.raises(SystemExit, match="equal males and females"):
            generate_teams(participants, PairingMode.MIXED, seed=1)


class TestMaleOnlyPairing:
    def test_valid(self) -> None:
        participants = _males(4) + _females(4)
        teams = generate_teams(participants, PairingMode.MALE_ONLY, seed=1)
        assert len(teams) == 2
        for t in teams:
            assert t.player1.gender == "male"
            assert t.player2.gender == "male"

    def test_impossible_odd_males(self) -> None:
        participants = _males(3) + _females(5)
        with pytest.raises(SystemExit, match="male_only"):
            generate_teams(participants, PairingMode.MALE_ONLY, seed=1)


class TestFemaleOnlyPairing:
    def test_valid(self) -> None:
        participants = _males(4) + _females(4)
        teams = generate_teams(participants, PairingMode.FEMALE_ONLY, seed=1)
        assert len(teams) == 2
        for t in teams:
            assert t.player1.gender == "female"
            assert t.player2.gender == "female"

    def test_impossible_odd_females(self) -> None:
        participants = _males(5) + _females(3)
        with pytest.raises(SystemExit, match="female_only"):
            generate_teams(participants, PairingMode.FEMALE_ONLY, seed=1)


class TestSameGenderPairing:
    def test_valid(self) -> None:
        participants = _males(4) + _females(4)
        teams = generate_teams(participants, PairingMode.SAME_GENDER, seed=1)
        assert len(teams) == 4
        for t in teams:
            assert t.player1.gender == t.player2.gender

    def test_impossible_odd_one_gender(self) -> None:
        participants = _males(3) + _females(4)
        with pytest.raises(SystemExit, match="odd number"):
            generate_teams(participants, PairingMode.SAME_GENDER, seed=1)


class TestRandomPairing:
    def test_valid(self) -> None:
        participants = _males(3) + _females(3)
        teams = generate_teams(participants, PairingMode.RANDOM, seed=1)
        assert len(teams) == 3

    def test_odd_count_error(self) -> None:
        participants = _males(3) + _females(2)
        with pytest.raises(SystemExit, match="odd number"):
            generate_teams(participants, PairingMode.RANDOM, seed=1)


class TestBalancing:
    def test_best_result_improves_spread(self) -> None:
        """100 attempts should find a better spread than a single random one."""
        participants = [
            _make("A", "male", 90),
            _make("B", "female", 10),
            _make("C", "male", 80),
            _make("D", "female", 20),
            _make("E", "male", 70),
            _make("F", "female", 30),
        ]
        teams = generate_teams(participants, PairingMode.RANDOM, seed=42, attempts=100)
        strengths = [t.pair_strength for t in teams]
        spread = max(strengths) - min(strengths)
        # Worst possible spread is 80 (90+80=170 vs 10+20=30 → 140, but realistic bad ~80)
        # With 100 attempts, spread should be very small
        assert spread <= 20

    def test_deterministic_with_seed(self) -> None:
        participants = _males(4) + _females(4)
        t1 = generate_teams(participants, PairingMode.RANDOM, seed=99)
        t2 = generate_teams(participants, PairingMode.RANDOM, seed=99)
        ids1 = [(t.player1.id, t.player2.id) for t in t1]
        ids2 = [(t.player1.id, t.player2.id) for t in t2]
        assert ids1 == ids2

    def test_team_ids_are_letters(self) -> None:
        participants = _males(3) + _females(3)
        teams = generate_teams(participants, PairingMode.RANDOM, seed=1)
        ids = [t.team_id for t in teams]
        assert ids == ["A", "B", "C"]


class TestFixedPairs:
    def test_fixed_pair_comes_first(self) -> None:
        p1 = _make("Alex", "male", 70)
        p2 = _make("Maria", "female", 60)
        p1.pair = 1
        p2.pair = 1
        rest = _males(2) + _females(2)
        teams = generate_teams([p1, p2] + rest, PairingMode.RANDOM, seed=1)
        # Fixed pair should be team A
        assert teams[0].player1.name == "Alex"
        assert teams[0].player2.name == "Maria"
        assert len(teams) == 3

    def test_multiple_fixed_pairs(self) -> None:
        p1 = _make("A1", "male", 70)
        p2 = _make("A2", "female", 60)
        p3 = _make("B1", "male", 50)
        p4 = _make("B2", "female", 40)
        p1.pair = 1
        p2.pair = 1
        p3.pair = 2
        p4.pair = 2
        rest = _males(2) + _females(2)
        teams = generate_teams([p1, p2, p3, p4] + rest, PairingMode.RANDOM, seed=1)
        assert len(teams) == 4
        assert teams[0].player1.name == "A1"
        assert teams[0].player2.name == "A2"
        assert teams[1].player1.name == "B1"
        assert teams[1].player2.name == "B2"

    def test_all_fixed(self) -> None:
        p1 = _make("A1", "male", 70)
        p2 = _make("A2", "female", 60)
        p1.pair = 1
        p2.pair = 1
        teams = generate_teams([p1, p2], PairingMode.RANDOM, seed=1)
        assert len(teams) == 1

    def test_invalid_pair_size(self) -> None:
        p1 = _make("A1", "male", 70)
        p2 = _make("A2", "female", 60)
        p3 = _make("A3", "male", 50)
        p1.pair = 1
        p2.pair = 1
        p3.pair = 1
        with pytest.raises(SystemExit, match="exactly 2"):
            generate_teams([p1, p2, p3], PairingMode.RANDOM, seed=1)

    def test_fixed_pairs_skip_mode_validation(self) -> None:
        """A fixed male+male pair should work even in mixed mode for the rest."""
        p1 = _make("M1", "male", 70)
        p2 = _make("M2", "male", 60)
        p1.pair = 1
        p2.pair = 1
        rest = _males(2) + _females(2)
        teams = generate_teams([p1, p2] + rest, PairingMode.MIXED, seed=1)
        assert len(teams) == 3
        # Fixed pair is male+male — allowed
        assert teams[0].player1.gender == "male"
        assert teams[0].player2.gender == "male"
        # Remaining pairs follow mixed mode
        for t in teams[1:]:
            genders = {t.player1.gender, t.player2.gender}
            assert genders == {"male", "female"}
