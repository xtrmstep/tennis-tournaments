from __future__ import annotations

import re

from models import Match


def assign_courts(matches: list[Match], num_courts: int) -> None:
    """Assign court numbers and time slots to matches in-place.

    Group-stage matches are scheduled first (as a complete phase), then
    knockout matches.  Within each phase the scheduler fills time slots
    respecting team-conflict and dependency constraints.
    """
    if num_courts < 1:
        raise SystemExit("Error: number of courts must be at least 1")

    group_matches = [m for m in matches if m.round_name.startswith("Group")]
    knockout_matches = [m for m in matches if not m.round_name.startswith("Group")]

    slot = _schedule_phase(group_matches, num_courts, start_slot=1)
    _schedule_phase(knockout_matches, num_courts, start_slot=slot)


def _schedule_phase(
    matches: list[Match], num_courts: int, start_slot: int,
) -> int:
    """Schedule a list of matches into slots. Returns the next free slot."""
    _REF = re.compile(r"(?:Winner|Loser) (M\d+)")

    scheduled: set[str] = set()
    remaining = list(matches)
    slot = start_slot

    while remaining:
        slot_matches: list[Match] = []
        busy_teams: set[str] = set()
        still_remaining: list[Match] = []

        for m in remaining:
            if len(slot_matches) >= num_courts:
                still_remaining.append(m)
                continue

            # Check dependency: referenced matches must already be scheduled
            deps = set(_REF.findall(m.team1) + _REF.findall(m.team2))
            if not deps.issubset(scheduled):
                still_remaining.append(m)
                continue

            # For group-stage matches, avoid team conflicts in same slot
            if m.round_name.startswith("Group"):
                if m.team1 in busy_teams or m.team2 in busy_teams:
                    still_remaining.append(m)
                    continue
                busy_teams.add(m.team1)
                busy_teams.add(m.team2)

            slot_matches.append(m)

        for i, m in enumerate(slot_matches):
            m.court = i + 1
            m.time_slot = slot
            scheduled.add(m.match_id)

        remaining = still_remaining
        slot += 1

    return slot
