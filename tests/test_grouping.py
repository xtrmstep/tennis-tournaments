from __future__ import annotations

import pytest

from bracket import generate_group_bracket
from grouping import create_groups, generate_group_matches, select_qualified_teams
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


class TestGroupBracket:
    def test_uses_group_labels(self) -> None:
        """Bracket for groups should use position labels, not team IDs."""
        teams = _teams(8)
        groups = create_groups(teams, group_size=4)
        matches = generate_group_bracket(groups, qualified_per_group=2)
        knockout = [m for m in matches if not m.round_name.startswith("Group")]
        semis = [m for m in knockout if m.round_name == "Semifinal"]
        assert len(semis) == 2
        # All team references in semis should be group-position labels
        all_labels = set()
        for sf in semis:
            all_labels.add(sf.team1)
            all_labels.add(sf.team2)
        for label in all_labels:
            assert "Group" in label

    def test_cross_group_matchups(self) -> None:
        """Group winners should face runners-up from other groups."""
        teams = _teams(8)
        groups = create_groups(teams, group_size=4)
        matches = generate_group_bracket(groups, qualified_per_group=2)
        knockout = [m for m in matches if not m.round_name.startswith("Group")]
        semis = [m for m in knockout if m.round_name == "Semifinal"]
        for sf in semis:
            # Extract group name from labels like '1st Group A'
            g1 = sf.team1.split("Group ")[1]
            g2 = sf.team2.split("Group ")[1]
            assert g1 != g2, f"{sf.match_id}: both teams from Group {g1}"

    def test_match_count_with_groups(self) -> None:
        teams = _teams(8)
        groups = create_groups(teams, group_size=4)
        matches = generate_group_bracket(groups, qualified_per_group=2)
        # Group stage: 2 groups × C(4,2) = 2×6 = 12 round-robin matches
        group_matches = [m for m in matches if m.round_name.startswith("Group")]
        assert len(group_matches) == 12
        # Knockout: 2 semis + 1 final + 1 third-place = 4
        knockout = [m for m in matches if not m.round_name.startswith("Group")]
        assert len(knockout) == 4
        # Total
        assert len(matches) == 16


class TestGroupMatches:
    def test_round_robin_match_count(self) -> None:
        """Each group of N teams produces N*(N-1)/2 matches."""
        teams = _teams(6)
        groups = create_groups(teams, group_size=3)  # 2 groups of 3
        matches = generate_group_matches(groups)
        # C(3,2) × 2 = 6
        assert len(matches) == 6

    def test_round_names_are_group_names(self) -> None:
        teams = _teams(4)
        groups = create_groups(teams, group_size=2)  # 2 groups of 2
        matches = generate_group_matches(groups)
        round_names = {m.round_name for m in matches}
        assert round_names == {"Group A", "Group B"}

    def test_uses_actual_team_ids(self) -> None:
        teams = _teams(4)
        groups = create_groups(teams, group_size=2)
        matches = generate_group_matches(groups)
        all_ids = {t.team_id for t in teams}
        for m in matches:
            assert m.team1 in all_ids
            assert m.team2 in all_ids

    def test_match_ids_sequential(self) -> None:
        teams = _teams(6)
        groups = create_groups(teams, group_size=3)
        matches = generate_group_matches(groups)
        for i, m in enumerate(matches, start=1):
            assert m.match_id == f"M{i}"
