# CLI Removal Instructions

Instructions for removing CLI capabilities from this repository while preserving the Flask + Vue web application.

## Prerequisites

- Confirm all tests pass before starting: `python -m pytest`
- Work on a dedicated branch

---

## Step 1 — Delete CLI-only files

Delete the following files entirely. They have no consumers in the backend or frontend:

- `main.py` — CLI entry point and orchestration
- `io_utils.py` — CSV input loading and file output writers (only called from `main.py`)
- `participants.csv` — sample CLI input file
- `grouping.py` — group-stage logic (only used in `main.py`)
- `bracket.py` — knockout bracket logic (only used in `main.py`)
- `scheduling.py` — court/time-slot assignment (only used in `main.py`)

---

## Step 2 — Delete CLI-only tests

Delete the following test files, which test only the deleted modules:

- `tests/test_cli.py` — tests `main.main()`
- `tests/test_grouping.py` — tests `grouping.py` and `bracket.py`
- `tests/test_bracket.py` — tests `bracket.py`
- `tests/test_scheduling.py` — tests `scheduling.py`

---

## Step 3 — Trim `models.py`

`models.py` (root, not `backend/models.py`) currently defines five dataclasses/enums. After removing the CLI modules, only three are still used by the backend (`backend/services/sorting_service.py`):

- `PairingMode` — keep
- `Participant` — keep
- `Team` — keep

Remove the following dataclasses, which exist solely to support the deleted CLI modules:

- `Group` — used only by `grouping.py` and `main.py`
- `Match` — used only by `bracket.py`, `scheduling.py`, and `main.py`

After editing, verify no remaining import of `Group` or `Match` exists anywhere:

```
grep -r "from models import" .
grep -r "import Group\|import Match" .
```

---

## Step 4 — Verify `pairing.py` is clean

`pairing.py` is kept because `backend/services/sorting_service.py` imports `generate_teams` from it. No changes are needed structurally, but confirm:

- It does not import from any deleted module (`io_utils`, `grouping`, `bracket`, `scheduling`, `main`)
- All its own imports resolve cleanly

---

## Step 5 — Update `README.md`

Remove or replace the following sections, which document CLI usage:

- The description line identifying this as a "CLI tool"
- The "Usage" / example `python main.py ...` commands
- The "CLI arguments" section listing all `--input`, `--output-dir`, `--pairing-mode`, etc. flags
- Any mention of output files (`teams.csv`, `groups.csv`, `matches.csv`, `summary.txt`)
- Any mention of `participants.csv` as input

Retain or update sections covering the web application, Docker setup, and API usage.

---

## Step 6 — Update `AGENTS.md`

Update the "High-Level Structure" section:

- Remove entries for: `main.py`, `io_utils.py`, `pairing.py` (CLI context), `grouping.py`, `bracket.py`, `scheduling.py`
- Remove entries for deleted test files
- Remove CLI-related bullet points from "Modification Guardrails" and "Dependent-Object Update Rules"
- Remove the CLI pyproject/requirements references if they only applied to CLI use

Keep all backend, frontend, Docker, and test entries that remain valid.

---

## Step 7 — Run verification

```bash
python -m pytest
```

Expected: only `tests/test_api.py`, `tests/test_pairing.py`, and `tests/test_sorting_service.py` run and pass.

Also confirm the Flask app starts cleanly:

```bash
python run.py
```

---

## Summary of what remains after removal

| Kept | Removed |
|---|---|
| `models.py` (trimmed) | `main.py` |
| `pairing.py` | `io_utils.py` |
| `run.py` | `grouping.py` |
| `backend/` (all) | `bracket.py` |
| `frontend/` (all) | `scheduling.py` |
| `tests/test_api.py` | `participants.csv` |
| `tests/test_pairing.py` | `tests/test_cli.py` |
| `tests/test_sorting_service.py` | `tests/test_grouping.py` |
| `requirements.txt` | `tests/test_bracket.py` |
| `pyproject.toml` | `tests/test_scheduling.py` |
| Docker files | |
