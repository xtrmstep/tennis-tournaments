from __future__ import annotations

import math

from models import Match, Team

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


def generate_bracket(teams: list[Team]) -> list[Match]:
    """Generate a single-elimination bracket structure.

    Supports any number of teams >= 2.  Non-power-of-2 counts get BYE slots so
    that the top-seeded teams receive first-round byes.
    """
    n = len(teams)
    if n < 2:
        raise SystemExit("Error: need at least 2 teams for a bracket")

    # Seed teams by pair_strength descending
    seeded = sorted(teams, key=lambda t: t.pair_strength, reverse=True)

    bracket_size = _next_power_of_two(n)
    num_byes = bracket_size - n

    # Build the first-round slots: team_id or "BYE"
    slots: list[str] = []
    for t in seeded:
        slots.append(t.team_id)
    slots.extend(["BYE"] * num_byes)

    # Arrange slots so byes are spread (simple approach: top seeds get byes at end)
    # Place seeds 1..bracket_size in standard bracket order:
    # For simplicity, pair slot 0 vs slot bracket_size-1, slot 1 vs slot bracket_size-2, etc.
    # This gives top seeds byes (since BYEs are at the end).
    first_round_pairs: list[tuple[str, str]] = []
    for i in range(bracket_size // 2):
        first_round_pairs.append((slots[i], slots[bracket_size - 1 - i]))

    matches: list[Match] = []
    match_counter = 1

    # Build first round (may include BYEs that auto-advance)
    current_round_sources: list[str] = []
    round_teams = bracket_size
    round_name = _round_name(round_teams)
    first_round_sf_ids: list[str] = []

    for a, b in first_round_pairs:
        if b == "BYE":
            current_round_sources.append(a)
        elif a == "BYE":
            current_round_sources.append(b)
        else:
            mid = f"M{match_counter}"
            matches.append(
                Match(
                    match_id=mid,
                    round_name=round_name,
                    team1=a,
                    team2=b,
                    source1=a,
                    source2=b,
                )
            )
            if round_name == "Semifinal":
                first_round_sf_ids.append(mid)
            current_round_sources.append(f"Winner {mid}")
            match_counter += 1

    # Build subsequent rounds
    while len(current_round_sources) > 1:
        round_teams = len(current_round_sources)
        round_name = _round_name(round_teams)
        next_sources: list[str] = []
        semifinal_match_ids: list[str] = []

        for i in range(0, len(current_round_sources), 2):
            s1 = current_round_sources[i]
            s2 = current_round_sources[i + 1]
            mid = f"M{match_counter}"

            matches.append(
                Match(
                    match_id=mid,
                    round_name=round_name,
                    team1=s1,
                    team2=s2,
                    source1=s1,
                    source2=s2,
                )
            )
            if round_name == "Semifinal":
                semifinal_match_ids.append(mid)
            next_sources.append(f"Winner {mid}")
            match_counter += 1

        current_round_sources = next_sources

        # Add 3rd-place match after semifinals
        if round_name == "Semifinal" and len(semifinal_match_ids) == 2:
            mid = f"M{match_counter}"
            matches.append(
                Match(
                    match_id=mid,
                    round_name="3rd Place",
                    team1=f"Loser {semifinal_match_ids[0]}",
                    team2=f"Loser {semifinal_match_ids[1]}",
                    source1=f"Loser {semifinal_match_ids[0]}",
                    source2=f"Loser {semifinal_match_ids[1]}",
                )
            )
            match_counter += 1

    # Handle case where the first round itself was the semifinal
    if first_round_sf_ids and len(first_round_sf_ids) == 2:
        # Check if we already added a 3rd-place match from the while loop
        has_third = any(m.round_name == "3rd Place" for m in matches)
        if not has_third:
            mid = f"M{match_counter}"
            matches.append(
                Match(
                    match_id=mid,
                    round_name="3rd Place",
                    team1=f"Loser {first_round_sf_ids[0]}",
                    team2=f"Loser {first_round_sf_ids[1]}",
                    source1=f"Loser {first_round_sf_ids[0]}",
                    source2=f"Loser {first_round_sf_ids[1]}",
                )
            )
            match_counter += 1
        if round_name == "Semifinal" and len(semifinal_match_ids) == 2:
            mid = f"M{match_counter}"
            matches.append(
                Match(
                    match_id=mid,
                    round_name="3rd Place",
                    team1=f"Loser {semifinal_match_ids[0]}",
                    team2=f"Loser {semifinal_match_ids[1]}",
                    source1=f"Loser {semifinal_match_ids[0]}",
                    source2=f"Loser {semifinal_match_ids[1]}",
                )
            )
            match_counter += 1

    return matches
