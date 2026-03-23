# Competition Reg — Pair Tennis Tournament Organizer

A simple Python CLI tool that organizes a pair tennis tournament from a CSV file of participants.

## What it does

1. Reads participants from a CSV file
2. Generates balanced 2-person teams respecting gender pairing rules
3. Optionally splits teams into groups (snake seeding)
4. Generates a single-elimination knockout bracket structure
5. Writes results to output files

## Input CSV format

```csv
name,gender,skill_percent
Alex,male,72
Maria,female,68
Ivan,male,61
Elena,female,75
```

**Required columns:** `name`, `gender`, `skill_percent`

**Optional columns:** `weight` (positive number)

- `gender` must be `male` or `female`
- `skill_percent` must be 0–100
- participant count must be even (to form 2-person teams)

## Usage

```bash
# Basic — random pairing
python main.py --input participants.csv --output-dir out

# Mixed pairing (male + female per team), deterministic
python main.py --input participants.csv --output-dir out --pairing-mode mixed --seed 42

# With group stage
python main.py --input participants.csv --output-dir out \
    --pairing-mode mixed --group-size 4 --qualified-per-group 2

# Same-gender pairing with groups
python main.py --input participants.csv --output-dir out \
    --pairing-mode same_gender --group-size 2 --qualified-per-group 1 --seed 7
```

## CLI arguments

| Argument | Required | Default | Description |
|---|---|---|---|
| `--input` | Yes | — | Path to participants CSV |
| `--output-dir` | Yes | — | Directory for output files |
| `--pairing-mode` | No | `random` | Team pairing mode (see below) |
| `--group-size` | No | — | Number of teams per group |
| `--qualified-per-group` | No | — | Teams qualifying from each group |
| `--seed` | No | — | Random seed for reproducibility |

## Pairing modes

| Mode | Rule |
|---|---|
| `random` | Any valid pairing |
| `mixed` | Each team is male + female |
| `male_only` | Each team is male + male |
| `female_only` | Each team is female + female |
| `same_gender` | Teams are either male+male or female+female |

## Output files

All files are written to `--output-dir`:

- **teams.csv** — Generated teams with player names, IDs, and pair strength
- **groups.csv** — Group assignments with qualification status (only if `--group-size` used)
- **matches.csv** — Knockout bracket structure (match IDs, rounds, team references)
- **summary.txt** — Human-readable tournament overview

## How to run tests

```bash
pip install pytest
pytest
```

## Requirements

- Python 3.12+
- No external dependencies (standard library only)
- `pytest` for tests
