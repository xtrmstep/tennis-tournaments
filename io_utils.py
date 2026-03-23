from __future__ import annotations

import csv
from pathlib import Path

from models import Group, Match, Participant, Team


def load_participants(path: Path) -> list[Participant]:
    """Read participants from a CSV file and validate all fields."""
    if not path.exists():
        raise SystemExit(f"Error: file not found: {path}")

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise SystemExit("Error: CSV file is empty or has no header row")

        fields = [name.strip() for name in reader.fieldnames]
        for required in ("name", "gender", "skill_percent"):
            if required not in fields:
                raise SystemExit(f"Error: missing required column '{required}' in CSV")

        has_weight = "weight" in fields
        participants: list[Participant] = []

        for i, row in enumerate(reader, start=1):
            name = row["name"].strip()
            if not name:
                raise SystemExit(f"Error: row {i}: name must not be empty")

            gender = row["gender"].strip().lower()
            if gender not in ("male", "female"):
                raise SystemExit(
                    f"Error: row {i}: gender must be 'male' or 'female', got '{gender}'"
                )

            try:
                skill = int(row["skill_percent"].strip())
            except (ValueError, TypeError):
                raise SystemExit(
                    f"Error: row {i}: skill_percent must be an integer"
                )
            if not 0 <= skill <= 100:
                raise SystemExit(
                    f"Error: row {i}: skill_percent must be between 0 and 100, got {skill}"
                )

            weight: float | None = None
            if has_weight and row.get("weight", "").strip():
                try:
                    weight = float(row["weight"].strip())
                except (ValueError, TypeError):
                    raise SystemExit(f"Error: row {i}: weight must be a number")
                if weight <= 0:
                    raise SystemExit(
                        f"Error: row {i}: weight must be positive, got {weight}"
                    )

            participants.append(
                Participant(
                    id=f"p{i}",
                    name=name,
                    gender=gender,
                    skill_percent=skill,
                    weight=weight,
                )
            )

    if len(participants) < 2:
        raise SystemExit("Error: need at least 2 participants to form a team")

    return participants


def write_teams_csv(teams: list[Team], output_dir: Path) -> None:
    path = output_dir / "teams.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["team_id", "player1_name", "player2_name", "player1_id", "player2_id", "pair_strength"]
        )
        for t in teams:
            writer.writerow(
                [t.team_id, t.player1.name, t.player2.name, t.player1.id, t.player2.id, t.pair_strength]
            )


def write_groups_csv(groups: list[Group], output_dir: Path) -> None:
    path = output_dir / "groups.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["group_name", "team_id", "pair_strength"])
        for g in groups:
            for t in sorted(g.teams, key=lambda x: x.pair_strength, reverse=True):
                writer.writerow([g.name, t.team_id, t.pair_strength])


def write_matches_csv(matches: list[Match], output_dir: Path) -> None:
    path = output_dir / "matches.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["match_id", "round_name", "team1", "team2"])
        for m in matches:
            writer.writerow([m.match_id, m.round_name, m.team1, m.team2])


def write_summary(
    *,
    participant_count: int,
    teams: list[Team],
    pairing_mode: str,
    groups: list[Group] | None,
    qualified_per_group: int | None,
    matches: list[Match],
    output_dir: Path,
) -> None:
    lines: list[str] = []
    lines.append("Tournament summary")
    lines.append("==================")
    lines.append("")
    lines.append(f"Participants: {participant_count}")
    lines.append(f"Teams: {len(teams)}")
    lines.append(f"Pairing mode: {pairing_mode}")

    if groups:
        lines.append("")
        lines.append("Groups:")
        for g in groups:
            team_ids = ", ".join(t.team_id for t in g.teams)
            lines.append(f"  - {g.name}: {team_ids}")
        lines.append("")
        lines.append(f"Qualification: top {qualified_per_group} per group advance to knockout")

    lines.append("")
    lines.append("Knockout:")
    for m in matches:
        lines.append(f"  - {m.match_id}: {m.team1} vs {m.team2}")

    lines.append("")
    path = output_dir / "summary.txt"
    path.write_text("\n".join(lines), encoding="utf-8")
