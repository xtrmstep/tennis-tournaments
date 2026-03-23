from __future__ import annotations

import argparse
import sys
from pathlib import Path

from bracket import generate_bracket
from grouping import create_groups, select_qualified_teams
from io_utils import (
    load_participants,
    write_groups_csv,
    write_matches_csv,
    write_summary,
    write_teams_csv,
)
from models import PairingMode
from pairing import generate_teams


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pair tennis tournament organizer"
    )
    parser.add_argument(
        "--input", required=True, type=Path, help="Path to participants CSV"
    )
    parser.add_argument(
        "--output-dir", required=True, type=Path, help="Directory for output files"
    )
    parser.add_argument(
        "--pairing-mode",
        type=str,
        default="random",
        choices=[m.value for m in PairingMode],
        help="Team pairing mode (default: random)",
    )
    parser.add_argument(
        "--group-size", type=int, default=None, help="Teams per group (optional)"
    )
    parser.add_argument(
        "--qualified-per-group",
        type=int,
        default=None,
        help="Teams qualifying from each group (optional)",
    )
    parser.add_argument(
        "--seed", type=int, default=None, help="Random seed for reproducibility"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    # 1. Load participants
    participants = load_participants(args.input)

    # 2. Generate teams
    mode = PairingMode(args.pairing_mode)
    teams = generate_teams(participants, mode, seed=args.seed)

    # 3. Optional group stage
    groups = None
    qualified_teams = None
    use_groups = args.group_size is not None

    if use_groups:
        if args.qualified_per_group is None:
            raise SystemExit(
                "Error: --qualified-per-group is required when --group-size is specified"
            )
        groups = create_groups(teams, args.group_size)
        qualified_teams = select_qualified_teams(groups, args.qualified_per_group)
        bracket_teams = qualified_teams
    else:
        if args.qualified_per_group is not None:
            raise SystemExit(
                "Error: --qualified-per-group requires --group-size"
            )
        bracket_teams = teams

    # 4. Generate bracket
    matches = generate_bracket(bracket_teams)

    # 5. Write output
    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    write_teams_csv(teams, output_dir)
    if groups is not None:
        qualified_ids = {t.team_id for t in (qualified_teams or [])}
        write_groups_csv(groups, qualified_ids, output_dir)
    write_matches_csv(matches, output_dir)
    write_summary(
        participant_count=len(participants),
        teams=teams,
        pairing_mode=args.pairing_mode,
        groups=groups,
        qualified_teams=qualified_teams,
        matches=matches,
        output_dir=output_dir,
    )

    print(f"Tournament generated successfully in {output_dir}/")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        if e.code and isinstance(e.code, str) and e.code.startswith("Error:"):
            print(e.code, file=sys.stderr)
            sys.exit(1)
        raise
