from __future__ import annotations

import pytest

from models import Match
from scheduling import assign_courts


def _group_matches() -> list[Match]:
    """Simulate 2 groups of 3: 3 matches per group = 6 total."""
    return [
        Match(match_id="M1", round_name="Group A", team1="A", team2="B"),
        Match(match_id="M2", round_name="Group A", team1="A", team2="C"),
        Match(match_id="M3", round_name="Group A", team1="B", team2="C"),
        Match(match_id="M4", round_name="Group B", team1="D", team2="E"),
        Match(match_id="M5", round_name="Group B", team1="D", team2="F"),
        Match(match_id="M6", round_name="Group B", team1="E", team2="F"),
    ]


def _knockout_matches(start: int = 1) -> list[Match]:
    """4-team knockout: 2 semis + final + 3rd place."""
    s = start
    return [
        Match(match_id=f"M{s}", round_name="Semifinal", team1="1st Group A", team2="2nd Group B"),
        Match(match_id=f"M{s+1}", round_name="Semifinal", team1="1st Group B", team2="2nd Group A"),
        Match(match_id=f"M{s+2}", round_name="Final", team1=f"Winner M{s}", team2=f"Winner M{s+1}"),
        Match(match_id=f"M{s+3}", round_name="3rd Place", team1=f"Loser M{s}", team2=f"Loser M{s+1}"),
    ]


class TestSingleCourt:
    def test_all_sequential(self) -> None:
        matches = _group_matches()
        assign_courts(matches, num_courts=1)
        # Every match on court 1, each in its own time slot
        for i, m in enumerate(matches, start=1):
            assert m.court == 1
            assert m.time_slot == i

    def test_knockout_sequential(self) -> None:
        matches = _knockout_matches()
        assign_courts(matches, num_courts=1)
        for m in matches:
            assert m.court == 1
        # All slots different
        slots = [m.time_slot for m in matches]
        assert len(set(slots)) == len(slots)


class TestTwoCourts:
    def test_group_parallel(self) -> None:
        matches = _group_matches()
        assign_courts(matches, num_courts=2)
        for m in matches:
            assert m.court in (1, 2)
            assert m.time_slot >= 1
        # With 2 courts and no team conflicts across groups, some slots
        # should have 2 matches
        from collections import Counter
        slot_counts = Counter(m.time_slot for m in matches)
        assert max(slot_counts.values()) == 2

    def test_no_team_conflict(self) -> None:
        matches = _group_matches()
        assign_courts(matches, num_courts=2)
        # Group matches by time slot and verify no team plays twice
        from collections import defaultdict
        slots: dict[int, list[Match]] = defaultdict(list)
        for m in matches:
            slots[m.time_slot].append(m)
        for slot_matches in slots.values():
            teams_in_slot: set[str] = set()
            for m in slot_matches:
                assert m.team1 not in teams_in_slot, f"team {m.team1} double-booked in slot"
                assert m.team2 not in teams_in_slot, f"team {m.team2} double-booked in slot"
                teams_in_slot.add(m.team1)
                teams_in_slot.add(m.team2)

    def test_knockout_semis_parallel(self) -> None:
        matches = _knockout_matches()
        assign_courts(matches, num_courts=2)
        semis = [m for m in matches if m.round_name == "Semifinal"]
        assert semis[0].time_slot == semis[1].time_slot
        assert semis[0].court != semis[1].court


class TestThreeCourts:
    def test_more_parallelism(self) -> None:
        matches = _group_matches()
        assign_courts(matches, num_courts=3)
        from collections import Counter
        slot_counts = Counter(m.time_slot for m in matches)
        # With 3 courts, first slot can have up to 3 non-conflicting matches
        assert max(slot_counts.values()) <= 3

    def test_no_team_conflict(self) -> None:
        matches = _group_matches()
        assign_courts(matches, num_courts=3)
        from collections import defaultdict
        slots: dict[int, list[Match]] = defaultdict(list)
        for m in matches:
            slots[m.time_slot].append(m)
        for slot_matches in slots.values():
            teams_in_slot: set[str] = set()
            for m in slot_matches:
                assert m.team1 not in teams_in_slot
                assert m.team2 not in teams_in_slot
                teams_in_slot.add(m.team1)
                teams_in_slot.add(m.team2)


class TestKnockoutDependencies:
    def test_final_after_semis(self) -> None:
        matches = _knockout_matches()
        assign_courts(matches, num_courts=2)
        semis = [m for m in matches if m.round_name == "Semifinal"]
        final = next(m for m in matches if m.round_name == "Final")
        assert final.time_slot > max(s.time_slot for s in semis)

    def test_third_place_after_semis(self) -> None:
        matches = _knockout_matches()
        assign_courts(matches, num_courts=2)
        semis = [m for m in matches if m.round_name == "Semifinal"]
        third = next(m for m in matches if m.round_name == "3rd Place")
        assert third.time_slot > max(s.time_slot for s in semis)

    def test_final_and_third_parallel_with_2_courts(self) -> None:
        matches = _knockout_matches()
        assign_courts(matches, num_courts=2)
        final = next(m for m in matches if m.round_name == "Final")
        third = next(m for m in matches if m.round_name == "3rd Place")
        # Both depend only on semis, so with 2 courts they can be parallel
        assert final.time_slot == third.time_slot
        assert final.court != third.court


class TestCombinedGroupAndKnockout:
    def test_knockout_after_group_stage(self) -> None:
        group = _group_matches()
        knockout = _knockout_matches(start=7)
        matches = group + knockout
        assign_courts(matches, num_courts=2)
        max_group_slot = max(m.time_slot for m in group)
        min_knockout_slot = min(m.time_slot for m in knockout)
        assert min_knockout_slot > max_group_slot


class TestEdgeCases:
    def test_invalid_zero_courts(self) -> None:
        with pytest.raises(SystemExit, match="at least 1"):
            assign_courts([], num_courts=0)

    def test_empty_match_list(self) -> None:
        matches: list[Match] = []
        assign_courts(matches, num_courts=2)
        assert matches == []
