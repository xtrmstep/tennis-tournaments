from __future__ import annotations

import math

from models import Group, Match, Team

# Round names by number of teams in that round
_ROUND_NAMES: dict[int, str] = {
    2: "Final",
    4: "Semifinal",
    8: "Quarterfinal",
}


def _round_name(teams_in_round: int) -> str:
    return _ROUND_NAMES.get(teams_in_round, f"Round of {teams_in_round}")


def _next_power_of_two(n: int) -> int:
    return 1 << (n - 1).bit_length()


def _ordinal(n: int) -> str:
    if n == 1:
        return "1st"
    if n == 2:
        return "2nd"
    if n == 3:
        return "3rd"
    return f"{n}th"


def _bracket_from_labels(labels: list[str]) -> list[Match]:
    """Build a single-elimination bracket from a list of slot labels."""
    n = len(labels)
    if n < 2:
        raise SystemExit("Error: need at least 2 slots for a bracket")

    bracket_size = _next_power_of_two(n)
    num_byes = bracket_size - n
    slots = list(labels) + ["BYE"] * num_byes

    first_round_pairs: list[tuple[str, str]] = []
    for i in range(bracket_size // 2):
        first_round_pairs.append((slots[i], slots[bracket_size - 1 - i]))

    matches: list[Match] = []
    match_counter = 1
    current_round_sources: list[str] = []
    round_teams = bracket_size
    rname = _round_name(round_teams)
    first_round_sf_ids: list[str] = []

    for a, b in first_round_pairs:
        if b == "BYE":
            current_round_sources.append(a)
        elif a == "BYE":
            current_round_sources.append(b)
        else:
            mid = f"M{match_counter}"
            matches.append(Match(
                match_id=mid, round_name=rname,
                team1=a, team2=b, source1=a, source2=b,
            ))
            if rname == "Semifinal":
                first_round_sf_ids.append(mid)
            current_round_sources.append(f"Winner {mid}")
            match_counter += 1

    while len(current_round_sources) > 1:
        round_teams = len(current_round_sources)
        rname = _round_name(round_teams)
        next_sources: list[str] = []
        semifinal_match_ids: list[str] = []

        for i in range(0, len(current_round_sources), 2):
            s1 = current_round_sources[i]
            s2 = current_round_sources[i + 1]
            mid = f"M{match_counter}"
            matches.append(Match(
                match_id=mid, round_name=rname,
                team1=s1, team2=s2, source1=s1, source2=s2,
            ))
            if rname == "Semifinal":
                semifinal_match_ids.append(mid)
            next_sources.append(f"Winner {mid}")
            match_counter += 1

        current_round_sources = next_sources

        if rname == "Semifinal" and len(semifinal_match_ids) == 2:
            mid = f"M{match_counter}"
            matches.append(Match(
                match_id=mid, round_name="3rd Place",
                team1=f"Loser {semifinal_match_ids[0]}",
                team2=f"Loser {semifinal_match_ids[1]}",
                source1=f"Loser {semifinal_match_ids[0]}",
                source2=f"Loser {semifinal_match_ids[1]}",
            ))
            match_counter += 1

    # Handle case where the first round itself was the semifinal
    if first_round_sf_ids and len(first_round_sf_ids) == 2:
        has_third = any(m.round_name == "3rd Place" for m in matches)
        if not has_third:
            mid = f"M{match_counter}"
            matches.append(Match(
                match_id=mid, round_name="3rd Place",
                team1=f"Loser {first_round_sf_ids[0]}",
                team2=f"Loser {first_round_sf_ids[1]}",
                source1=f"Loser {first_round_sf_ids[0]}",
                source2=f"Loser {first_round_sf_ids[1]}",
            ))

    return matches


def generate_bracket(teams: list[Team]) -> list[Match]:
    """Generate a single-elimination bracket from teams, seeded by pair_strength."""
    if len(teams) < 2:
        raise SystemExit("Error: need at least 2 teams for a bracket")

    seeded = sorted(teams, key=lambda t: t.pair_strength, reverse=True)
    labels = [t.team_id for t in seeded]
    return _bracket_from_labels(labels)


def generate_group_bracket(
    groups: list[Group], qualified_per_group: int
) -> list[Match]:
    """Generate a bracket using group-position labels instead of actual team IDs.

    Produces matches like '1st Group A vs 2nd Group B' so the bracket
    describes the tournament structure without pre-determining results.
    """
    if qualified_per_group < 1:
        raise SystemExit("Error: qualified_per_group must be at least 1")
    for g in groups:
        if qualified_per_group > len(g.teams):
            raise SystemExit(
                f"Error: qualified_per_group ({qualified_per_group}) exceeds "
                f"teams in {g.name} ({len(g.teams)})"
            )

    # Build labels in cross-group seeded order:
    # all rank-1 seeds in group order, then rank-2 seeds, etc.
    labels: list[str] = []
    for rank in range(qualified_per_group):
        for g in groups:
            labels.append(f"{_ordinal(rank + 1)} {g.name}")

    return _bracket_from_labels(labels)
