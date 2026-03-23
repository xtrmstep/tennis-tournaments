from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class PairingMode(StrEnum):
    MIXED = "mixed"
    MALE_ONLY = "male_only"
    FEMALE_ONLY = "female_only"
    SAME_GENDER = "same_gender"
    RANDOM = "random"


@dataclass
class Participant:
    id: str
    name: str
    gender: str
    skill_percent: int
    weight: float | None = None


@dataclass
class Team:
    team_id: str
    player1: Participant
    player2: Participant
    pair_strength: int = field(init=False)

    def __post_init__(self) -> None:
        self.pair_strength = self.player1.skill_percent + self.player2.skill_percent


@dataclass
class Group:
    name: str
    teams: list[Team]


@dataclass
class Match:
    match_id: str
    round_name: str
    team1: str
    team2: str
    court: int = 0
    time_slot: int = 0
