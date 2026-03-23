from __future__ import annotations

import pytest

from grouping import create_groups, select_qualified_teams
from models import Participant, Team


def _team(tid: str, strength: int) -> Team:
    p1 = Participant(id="p1", name="A", gender="male", skill_percent=strength // 2)
    p2 = Participant(id="p2", name="B", gender="female", skill_percent=strength - strength // 2)
    t = Team(team_id=tid, player1=p1, player2=p2)
    return t


def _teams(n: int) -> list[Team]:
    """Create n teams with decreasing strength: 200, 190, 180, ..."""
    return [_team(chr(65 + i), 200 - i * 10) for i in range(n)]


class TestCreateGroups:
    def test_correct_number_of_groups(self) -> None:
        teams = _teams(8)
        groups = create_groups(teams, group_size=4)
        assert len(groups) == 2

    def test_group_names(self) -> None:
        teams = _teams(6)
        groups = create_groups(teams, group_size=3)
        assert [g.name for g in groups] == ["Group A", "Group B"]

    def test_snake_distribution_balances_groups(self) -> None:
        teams = _teams(8)
        groups = create_groups(teams, group_size=4)
        # Snake: strongest seeds split across groups
        strength_a = sum(t.pair_strength for t in groups[0].teams)
        strength_b = sum(t.pair_strength for t in groups[1].teams)
        # With snake seeding, groups should be close in total strength
        assert abs(strength_a - strength_b) <= 20

    def test_each_group_has_correct_size(self) -> None:
        teams = _teams(9)
        groups = create_groups(teams, group_size=3)
        assert len(groups) == 3
        for g in groups:
            assert len(g.teams) == 3

    def test_invalid_group_size_too_small(self) -> None:
        teams = _teams(4)
        with pytest.raises(SystemExit, match="at least 2"):
            create_groups(teams, group_size=1)

    def test_invalid_uneven_division(self) -> None:
        teams = _teams(5)
        with pytest.raises(SystemExit, match="evenly divided"):
            create_groups(teams, group_size=3)

    def test_not_enough_teams(self) -> None:
        teams = _teams(2)
        with pytest.raises(SystemExit, match="not enough teams"):
            create_groups(teams, group_size=4)


class TestSelectQualified:
    def test_correct_count(self) -> None:
        teams = _teams(8)
        groups = create_groups(teams, group_size=4)
        qualified = select_qualified_teams(groups, qualified_per_group=2)
        assert len(qualified) == 4

    def test_top_teams_selected(self) -> None:
        teams = _teams(4)
        groups = create_groups(teams, group_size=2)
        qualified = select_qualified_teams(groups, qualified_per_group=1)
        # Should pick the strongest team from each group
        for q in qualified:
            group = next(g for g in groups if q in g.teams)
            group_strengths = sorted(
                [t.pair_strength for t in group.teams], reverse=True
            )
            assert q.pair_strength == group_strengths[0]

    def test_invalid_qualified_per_group_zero(self) -> None:
        teams = _teams(4)
        groups = create_groups(teams, group_size=2)
        with pytest.raises(SystemExit, match="at least 1"):
            select_qualified_teams(groups, qualified_per_group=0)

    def test_invalid_qualified_exceeds_group(self) -> None:
        teams = _teams(4)
        groups = create_groups(teams, group_size=2)
        with pytest.raises(SystemExit, match="exceeds"):
            select_qualified_teams(groups, qualified_per_group=5)
