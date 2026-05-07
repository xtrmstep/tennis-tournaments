# Repository Overview

This repository is a Python 3.12 CLI for organizing pair tennis tournaments from a participants CSV file. It loads and validates participants, creates teams according to pairing rules, optionally creates group-stage round robins, builds a knockout bracket, assigns courts and time slots, and writes CSV/text outputs. Most agent work here should stay focused on tournament logic, shared models, CLI/input-output behavior, and the related tests and documentation.

## High-Level Structure

- `main.py` — CLI entry point that orchestrates input loading, team generation, optional group-stage flow, bracket generation, scheduling, and output writing.
- `models.py` — shared dataclasses and enums used across the repository.
- `io_utils.py` — participant CSV parsing/validation and output file generation.
- `pairing.py` — team creation rules, including pairing modes, fixed pairs, and balance logic.
- `grouping.py` — group creation, round-robin match generation, qualification, and group seeding rules.
- `bracket.py` — knockout bracket generation and group-to-bracket transition logic.
- `scheduling.py` — court and time-slot assignment for matches, including dependency-aware ordering.
- `tests/` — pytest coverage for the CLI and the main domain modules.
- `README.md` — user-facing usage, input format, outputs, and test instructions.
- `pyproject.toml` — project metadata and pytest configuration.

## Modification Guardrails

- Keep changes limited to the requested scope.
- Preserve existing behavior unless the requested change explicitly requires different behavior.
- Reuse existing patterns, models, and module boundaries before introducing new ones.
- Apply DRY and SOLID principles where they fit the current design.
- Avoid duplication, hidden coupling, and large unrelated refactoring.
- Check the existing implementation and test patterns before adding new APIs, names, or file layouts.
- Do not add new runtime dependencies, frameworks, or architectural layers without a clear repository-supported reason.

## Dependent-Object Update Rules

- When changing shared models or enum values in `models.py`, update all affected modules, CLI handling, writers, and tests together.
- When changing CLI arguments in `main.py` or CSV/output handling in `io_utils.py`, also update the related CLI tests and `README.md`.
- When changing pairing behavior in `pairing.py`, verify downstream effects on grouping, bracket generation, summaries/outputs, and tests that depend on team composition or strength ordering.
- When changing group-stage behavior in `grouping.py`, also check bracket qualification/seeding in `bracket.py`, scheduling assumptions in `scheduling.py`, and the related tests.
- When changing knockout behavior in `bracket.py`, also verify inputs from grouping, scheduling expectations, and output formatting/tests.
- When changing scheduling behavior in `scheduling.py`, also review match output expectations and tests for court assignment, time slots, and dependency ordering.
- When adding a new major workflow or object, place it with the existing module that owns that responsibility and add/update focused tests and documentation where user-visible behavior changes.
- When removing or renaming CLI options, CSV fields, output columns, or output files, update dependent tests and documentation in the same change.

## Testing and Verification

- Use the existing test command for repository verification: `python -m pytest`.
- Keep verification proportional to the change; run targeted checks while iterating and the relevant full test suite before finishing.
- Add or update tests in `tests/` whenever behavior changes or new rules are introduced.
- For documentation-only changes, verify that the documented commands, modules, and responsibilities still match the repository state and note any manual checks performed.

## Style and Documentation Rules

- Follow the existing Python 3.12 style, naming, and module organization already present in the repository.
- Keep new code and documentation concise, factual, and behavior-focused.
- Extend existing modules and tests instead of creating parallel patterns for the same responsibility.
- Match the repository’s current naming and folder conventions before introducing new structure.
- Keep comments and documentation short and useful; avoid narrative or marketing-style text.
