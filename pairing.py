from __future__ import annotations

import random
import string

from collections import defaultdict

from models import Participant, PairingMode, Team


def _team_id(index: int) -> str:
    """Return a team ID letter: 0->A, 1->B, ..., 25->Z."""
    return string.ascii_uppercase[index]


def _spread(teams: list[Team]) -> int:
    """Balance metric: difference between strongest and weakest team."""
    strengths = [t.pair_strength for t in teams]
    return max(strengths) - min(strengths)


def _validate_pairing_possible(
    participants: list[Participant], mode: PairingMode
) -> None:
    n = len(participants)
    if n % 2 != 0:
        raise SystemExit(
            f"Error: odd number of participants ({n}), cannot form pairs"
        )
    if n < 2:
        raise SystemExit("Error: need at least 2 participants")

    males = [p for p in participants if p.gender == "male"]
    females = [p for p in participants if p.gender == "female"]

    if mode == PairingMode.MIXED:
        # Mixed creates as many M+F pairs as possible, then pairs leftovers.
        # Only requirement: even total count (already checked above).
        pass
    elif mode == PairingMode.MALE_ONLY:
        if len(males) < 2 or len(males) % 2 != 0:
            raise SystemExit(
                f"Error: male_only mode requires an even number of males (>=2), "
                f"got {len(males)}"
            )
    elif mode == PairingMode.FEMALE_ONLY:
        if len(females) < 2 or len(females) % 2 != 0:
            raise SystemExit(
                f"Error: female_only mode requires an even number of females (>=2), "
                f"got {len(females)}"
            )
    elif mode == PairingMode.SAME_GENDER:
        if len(males) % 2 != 0:
            raise SystemExit(
                f"Error: same_gender mode requires even number of males, got {len(males)}"
            )
        if len(females) % 2 != 0:
            raise SystemExit(
                f"Error: same_gender mode requires even number of females, got {len(females)}"
            )
        if len(males) + len(females) < 2:
            raise SystemExit("Error: not enough participants for same_gender mode")


def _build_teams_from_pairs(pairs: list[tuple[Participant, Participant]]) -> list[Team]:
    return [
        Team(team_id=_team_id(i), player1=a, player2=b)
        for i, (a, b) in enumerate(pairs)
    ]


def _try_mixed(males: list[Participant], females: list[Participant], rng: random.Random) -> list[Team]:
    m = list(males)
    f = list(females)
    rng.shuffle(m)
    rng.shuffle(f)
    mixed_count = min(len(m), len(f))
    pairs: list[tuple[Participant, Participant]] = list(zip(m[:mixed_count], f[:mixed_count]))
    leftover = m[mixed_count:] + f[mixed_count:]
    rng.shuffle(leftover)
    for i in range(0, len(leftover), 2):
        pairs.append((leftover[i], leftover[i + 1]))
    return _build_teams_from_pairs(pairs)


def _try_single_gender(pool: list[Participant], rng: random.Random) -> list[Team]:
    p = list(pool)
    rng.shuffle(p)
    pairs = [(p[i], p[i + 1]) for i in range(0, len(p), 2)]
    return _build_teams_from_pairs(pairs)


def _try_random(participants: list[Participant], rng: random.Random) -> list[Team]:
    p = list(participants)
    rng.shuffle(p)
    pairs = [(p[i], p[i + 1]) for i in range(0, len(p), 2)]
    return _build_teams_from_pairs(pairs)


def _extract_fixed_pairs(
    participants: list[Participant],
) -> tuple[list[Team], list[Participant]]:
    """Split participants into pre-assigned teams and remaining pool.

    Participants with a `pair` value are grouped by that number.
    Each group must have exactly 2 members.
    """
    by_pair: dict[int, list[Participant]] = defaultdict(list)
    remaining: list[Participant] = []

    for p in participants:
        if p.pair is not None:
            by_pair[p.pair].append(p)
        else:
            remaining.append(p)

    fixed_teams: list[Team] = []
    for pair_num, members in sorted(by_pair.items()):
        if len(members) != 2:
            raise SystemExit(
                f"Error: pair {pair_num} must have exactly 2 participants, "
                f"got {len(members)}"
            )
        fixed_teams.append(
            Team(team_id="", player1=members[0], player2=members[1])
        )

    return fixed_teams, remaining


def generate_teams(
    participants: list[Participant],
    pairing_mode: PairingMode,
    seed: int | None = None,
    attempts: int = 100,
) -> list[Team]:
    """Generate balanced 2-person teams respecting the pairing mode.

    Participants with a `pair` value are paired first; the remaining
    participants go through normal mode-based pairing.
    """
    fixed_teams, remaining = _extract_fixed_pairs(participants)

    if remaining:
        _validate_pairing_possible(remaining, pairing_mode)

        rng = random.Random(seed)
        males = [p for p in remaining if p.gender == "male"]
        females = [p for p in remaining if p.gender == "female"]

        best: list[Team] | None = None
        best_spread: int = 999_999

        for _ in range(attempts):
            if pairing_mode == PairingMode.MIXED:
                candidate = _try_mixed(males, females, rng)
            elif pairing_mode == PairingMode.MALE_ONLY:
                candidate = _try_single_gender(males, rng)
            elif pairing_mode == PairingMode.FEMALE_ONLY:
                candidate = _try_single_gender(females, rng)
            elif pairing_mode == PairingMode.SAME_GENDER:
                male_teams = _try_single_gender(males, rng) if len(males) >= 2 else []
                female_teams = _try_single_gender(females, rng) if len(females) >= 2 else []
                all_pairs: list[tuple[Participant, Participant]] = []
                for t in male_teams:
                    all_pairs.append((t.player1, t.player2))
                for t in female_teams:
                    all_pairs.append((t.player1, t.player2))
                candidate = _build_teams_from_pairs(all_pairs)
            else:  # random
                candidate = _try_random(remaining, rng)

            spread = _spread(candidate)
            if spread < best_spread:
                best_spread = spread
                best = candidate

        assert best is not None
        generated = best
    else:
        generated = []

    all_teams = fixed_teams + generated
    # Assign clean team IDs: A, B, C, ...
    for i, team in enumerate(all_teams):
        team.team_id = _team_id(i)
    return all_teams
