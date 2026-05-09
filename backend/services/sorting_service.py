from __future__ import annotations

from pairing import generate_teams
from models import Participant, PairingMode


def run_sorting(people: list, mode: str, seed: int | None = None) -> list[dict]:
    """Sort people by mode and return serializable result items."""
    if mode == "singles":
        return _sort_singles(people)
    if mode == "doubles":
        return _sort_doubles(people, seed)
    raise ValueError(f"Invalid sorting mode: {mode!r}")


def _sort_singles(people: list) -> list[dict]:
    def _key(p):
        # None rating sorts last
        return (p.rating is None, -(p.rating or 0))

    sorted_people = sorted(people, key=_key)
    return [p.to_dict() for p in sorted_people]


def _sort_doubles(people: list, seed: int | None) -> list[dict]:
    if len(people) < 2:
        raise ValueError("Need at least 2 people for doubles sorting")
    if len(people) % 2 != 0:
        raise ValueError(
            f"Need an even number of people for doubles; got {len(people)}"
        )

    participants = [
        Participant(
            id=str(p.id),
            name=p.name,
            gender="male",
            skill_percent=(p.rating or 5) * 10,
        )
        for p in people
    ]

    # Build id→person lookup for enriching team dicts
    id_to_person = {p.id: p for p in people}

    kwargs: dict = {"attempts": 100}
    if seed is not None:
        kwargs["seed"] = seed

    teams = generate_teams(participants, PairingMode.RANDOM, **kwargs)

    result = []
    for team in teams:
        p1_id = int(team.player1.id)
        p2_id = int(team.player2.id)
        person1 = id_to_person.get(p1_id)
        person2 = id_to_person.get(p2_id)
        result.append(
            {
                "team_id": team.team_id,
                "player1": person1.to_dict() if person1 else {"id": p1_id},
                "player2": person2.to_dict() if person2 else {"id": p2_id},
                "pair_strength": team.pair_strength,
            }
        )
    return result
