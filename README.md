# Competition Reg — Pair Tennis Tournament Organizer

A simple Python CLI tool that organizes a pair tennis tournament from a CSV file of participants.

## What it does

1. Reads participants from a CSV file
2. Generates balanced 2-person teams respecting gender pairing rules
3. Optionally splits teams into groups (snake seeding) with round-robin matches
4. Generates a single-elimination knockout bracket structure
5. Assigns matches to courts and time slots
6. Writes results to output files

## Input CSV format

```csv
name,gender,skill_percent
Alex,male,72
Maria,female,68
Ivan,male,61
Elena,female,75
```

**Required columns:** `name`, `gender`, `skill_percent`

**Optional columns:** `weight` (positive number), `pair` (positive integer)

- `gender` must be `male` or `female`
- `skill_percent` must be 0–100
- participant count must be even (to form 2-person teams)
- `pair` — participants sharing the same number are pre-assigned as a team (each number must appear exactly twice)

## Usage

```bash
# Basic — random pairing
python main.py --input participants.csv --output-dir out

# Mixed pairing (male + female per team), deterministic
python main.py --input participants.csv --output-dir out --pairing-mode mixed --seed 42

# With group stage
python main.py --input participants.csv --output-dir out \
    --pairing-mode mixed --group-size 4 --qualified-per-group 2

# With 2 courts for parallel play
python main.py --input participants.csv --output-dir out \
    --pairing-mode mixed --group-size 4 --qualified-per-group 2 --courts 2

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
| `--courts` | No | `1` | Number of available courts |

## Pairing modes

| Mode | Rule |
|---|---|
| `random` | Any valid pairing |
| `mixed` | As many male+female pairs as possible; leftover same-gender participants are paired together |
| `male_only` | Each team is male + male |
| `female_only` | Each team is female + female |
| `same_gender` | Teams are either male+male or female+female |

## Pre-assigned pairs

Add a `pair` column to the CSV to lock specific participants together:

```csv
name,gender,skill_percent,pair
Alex,male,72,1
Maria,female,68,1
Ivan,male,61,
Elena,female,75,
```

Alex and Maria will always be teamed (pair 1). Ivan and Elena go through normal pairing. Pre-assigned pairs bypass the pairing mode — a male+male fixed pair is allowed even in mixed mode.

## Court allocation

Use `--courts N` to configure the number of available courts:

- **1 court** (default): all matches are played sequentially
- **2 courts**: up to 2 matches run in parallel per time slot
- **3 courts**: up to 3 matches run in parallel per time slot

The scheduler ensures:
- No team plays on two courts in the same time slot
- Knockout matches respect dependencies (e.g., the Final waits for both Semifinals to finish)

Each match in the output includes its `court` number and `time_slot`.

## Output files

All files are written to `--output-dir`:

- **teams.csv** — Generated teams with player names, IDs, and pair strength
- **groups.csv** — Group assignments (only if `--group-size` used)
- **matches.csv** — Full schedule: group-stage round-robin and knockout bracket, with court and time slot assignments
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

## Web Application

A Flask + Vue 3 web UI for managing participants and running sorting.

### Requirements

- Python 3.12+
- Node.js 18+

### Backend setup

```bash
pip install -r requirements.txt
python run.py
```

Runs on http://localhost:5000.

### Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Runs on http://localhost:5173. All `/api` requests are proxied to the backend.

### Environment variables

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | `dev-secret-change-in-production` | Flask session signing key |
| `DATABASE_URL` | `sqlite:///app.db` | SQLAlchemy database URI |

### How to use

1. Open http://localhost:5173 and sign up for an account.
2. Go to **People** and add participants (name, optional skill, optional photo).
3. Assign a **rating** (1–10) to each person.
4. Go to **Sorting** and choose a mode:
   - **Singles**: ranks all people by rating, highest first.
   - **Doubles**: pairs people into balanced teams using the tournament pairing engine; requires an even number of people.
5. Click **Run Sorting** to generate and save the result.
