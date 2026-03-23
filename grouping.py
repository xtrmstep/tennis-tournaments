from __future__ import annotations

import itertools
import string

from models import Group, Match, Team


def generate_group_matches(
    groups: list[Group], match_start: int = 1,
) -> list[Match]:
    """Generate round-robin matches within each group."""
    matches: list[Match] = []
    counter = match_start
    for g in groups:
        for t1, t2 in itertools.combinations(g.teams, 2):
            matches.append(Match(
                match_id=f"M{counter}",
                round_name=g.name,
                team1=t1.team_id,
                team2=t2.team_id,
            ))
            counter += 1
    return matches


def create_groups(teams: list[Team], group_size: int) -> list[Group]:
    """Split teams into groups using snake seeding by pair_strength."""
    n = len(teams)
    if group_size < 2:
        raise SystemExit("Error: group_size must be at least 2")
    if n < group_size:
        raise SystemExit(
            f"Error: not enough teams ({n}) for group_size {group_size}"
        )
    if n % group_size != 0:
        raise SystemExit(
            f"Error: {n} teams cannot be evenly divided into groups of {group_size}"
        )

    num_groups = n // group_size
    sorted_teams = sorted(teams, key=lambda t: t.pair_strength, reverse=True)

    # Initialize groups
    groups: list[Group] = [
        Group(name=f"Group {string.ascii_uppercase[i]}", teams=[])
        for i in range(num_groups)
    ]

    # Snake-seed: forward pass then reverse pass
    direction = 1
    group_idx = 0
    for team in sorted_teams:
        groups[group_idx].teams.append(team)
        # Advance with snake logic
        next_idx = group_idx + direction
        if next_idx >= num_groups or next_idx < 0:
            direction *= -1  # reverse
        else:
            group_idx = next_idx

    return groups


def select_qualified_teams(
    groups: list[Group], qualified_per_group: int
) -> list[Team]:
    """Select top N teams per group by pair_strength."""
    if qualified_per_group < 1:
        raise SystemExit("Error: qualified_per_group must be at least 1")

    for g in groups:
        if qualified_per_group > len(g.teams):
            raise SystemExit(
                f"Error: qualified_per_group ({qualified_per_group}) exceeds "
                f"teams in {g.name} ({len(g.teams)})"
            )

    qualified: list[Team] = []
    for g in groups:
        ranked = sorted(g.teams, key=lambda t: t.pair_strength, reverse=True)
        qualified.extend(ranked[:qualified_per_group])
    return qualified


def seed_qualified_for_bracket(
    groups: list[Group], qualified_per_group: int
) -> list[Team]:
    """Order qualified teams for the bracket to avoid same-group matchups.

    Lists all rank-1 seeds in group order, then rank-2 seeds in group order,
    etc.  Combined with the bracket's top-vs-bottom pairing this ensures group
    winners face runners-up from other groups.
    """
    ranked_per_group: list[list[Team]] = []
    for g in groups:
        ranked = sorted(g.teams, key=lambda t: t.pair_strength, reverse=True)
        ranked_per_group.append(ranked[:qualified_per_group])

    seeded: list[Team] = []
    for rank in range(qualified_per_group):
        for gi in range(len(groups)):
            seeded.append(ranked_per_group[gi][rank])
    return seeded
