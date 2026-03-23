from __future__ import annotations

import csv
import os
from pathlib import Path

import pytest

from main import main


@pytest.fixture()
def sample_csv(tmp_path: Path) -> Path:
    """Create a valid 8-participant CSV (4 male, 4 female)."""
    path = tmp_path / "participants.csv"
    path.write_text(
        "name,gender,skill_percent\n"
        "Alex,male,72\n"
        "Maria,female,68\n"
        "Ivan,male,61\n"
        "Elena,female,75\n"
        "Sergei,male,55\n"
        "Olga,female,80\n"
        "Dmitri,male,65\n"
        "Natasha,female,58\n",
        encoding="utf-8",
    )
    return path


@pytest.fixture()
def bad_csv(tmp_path: Path) -> Path:
    path = tmp_path / "bad.csv"
    path.write_text(
        "name,gender,skill_percent\n"
        "Alex,male,72\n"
        "Maria,alien,68\n",
        encoding="utf-8",
    )
    return path


@pytest.fixture()
def odd_csv(tmp_path: Path) -> Path:
    path = tmp_path / "odd.csv"
    path.write_text(
        "name,gender,skill_percent\n"
        "Alex,male,72\n"
        "Maria,female,68\n"
        "Ivan,male,61\n",
        encoding="utf-8",
    )
    return path


class TestCLISuccess:
    def test_basic_run(self, sample_csv: Path, tmp_path: Path) -> None:
        out = tmp_path / "out"
        main(["--input", str(sample_csv), "--output-dir", str(out)])
        assert (out / "teams.csv").exists()
        assert (out / "matches.csv").exists()
        assert (out / "summary.txt").exists()

    def test_mixed_mode(self, sample_csv: Path, tmp_path: Path) -> None:
        out = tmp_path / "out"
        main([
            "--input", str(sample_csv),
            "--output-dir", str(out),
            "--pairing-mode", "mixed",
            "--seed", "42",
        ])
        # Verify teams.csv has correct columns
        with open(out / "teams.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 4
        assert "team_id" in reader.fieldnames
        assert "pair_strength" in reader.fieldnames

    def test_with_groups(self, sample_csv: Path, tmp_path: Path) -> None:
        out = tmp_path / "out"
        main([
            "--input", str(sample_csv),
            "--output-dir", str(out),
            "--pairing-mode", "random",
            "--group-size", "2",
            "--qualified-per-group", "1",
            "--seed", "42",
        ])
        assert (out / "groups.csv").exists()
        assert (out / "matches.csv").exists()
        # Matches should include group-stage round-robin matches
        matches_text = (out / "matches.csv").read_text(encoding="utf-8")
        assert "Group" in matches_text
        # Summary should show group stage and qualification rule
        summary = (out / "summary.txt").read_text(encoding="utf-8")
        assert "Group stage:" in summary
        assert "top 1 per group advance to knockout" in summary

    def test_summary_content(self, sample_csv: Path, tmp_path: Path) -> None:
        out = tmp_path / "out"
        main(["--input", str(sample_csv), "--output-dir", str(out), "--seed", "1"])
        summary = (out / "summary.txt").read_text(encoding="utf-8")
        assert "Participants: 8" in summary
        assert "Teams: 4" in summary


class TestCLIFailure:
    def test_invalid_csv_gender(self, bad_csv: Path, tmp_path: Path) -> None:
        out = tmp_path / "out"
        with pytest.raises(SystemExit, match="gender"):
            main(["--input", str(bad_csv), "--output-dir", str(out)])

    def test_file_not_found(self, tmp_path: Path) -> None:
        out = tmp_path / "out"
        with pytest.raises(SystemExit, match="file not found"):
            main(["--input", str(tmp_path / "nope.csv"), "--output-dir", str(out)])

    def test_impossible_pairing(self, odd_csv: Path, tmp_path: Path) -> None:
        out = tmp_path / "out"
        with pytest.raises(SystemExit, match="odd number"):
            main([
                "--input", str(odd_csv),
                "--output-dir", str(out),
                "--pairing-mode", "mixed",
            ])

    def test_group_without_qualified(self, sample_csv: Path, tmp_path: Path) -> None:
        out = tmp_path / "out"
        with pytest.raises(SystemExit, match="qualified-per-group is required"):
            main([
                "--input", str(sample_csv),
                "--output-dir", str(out),
                "--group-size", "2",
            ])
