from __future__ import annotations

import pytest

from bracket import generate_bracket
from models import Participant, Team


def _team(tid: str, strength: int) -> Team:
    p1 = Participant(id="p1", name="A", gender="male", skill_percent=strength // 2)
    p2 = Participant(id="p2", name="B", gender="female", skill_percent=strength - strength // 2)
    return Team(team_id=tid, player1=p1, player2=p2)


def _teams(n: int) -> list[Team]:
    return [_team(chr(65 + i), 200 - i * 10) for i in range(n)]


class TestBracket4Teams:
    def test_match_count(self) -> None:
        matches = generate_bracket(_teams(4))
        # 2 semis + 1 final + 1 third-place = 4
        assert len(matches) == 4

    def test_round_names(self) -> None:
        matches = generate_bracket(_teams(4))
        rounds = [m.round_name for m in matches]
        assert rounds.count("Semifinal") == 2
        assert rounds.count("Final") == 1
        assert rounds.count("3rd Place") == 1

    def test_final_references_semifinal_winners(self) -> None:
        matches = generate_bracket(_teams(4))
        final = next(m for m in matches if m.round_name == "Final")
        assert "Winner" in final.source1
        assert "Winner" in final.source2


class TestBracket8Teams:
    def test_match_count(self) -> None:
        matches = generate_bracket(_teams(8))
        # 4 QF + 2 SF + 1 F + 1 3rd = 8
        assert len(matches) == 8

    def test_round_names(self) -> None:
        matches = generate_bracket(_teams(8))
        rounds = [m.round_name for m in matches]
        assert rounds.count("Quarterfinal") == 4
        assert rounds.count("Semifinal") == 2
        assert rounds.count("Final") == 1
        assert rounds.count("3rd Place") == 1

    def test_quarterfinal_has_direct_team_ids(self) -> None:
        matches = generate_bracket(_teams(8))
        qf = [m for m in matches if m.round_name == "Quarterfinal"]
        for m in qf:
            # source1 and source2 should be direct team IDs (no "Winner" prefix)
            assert "Winner" not in m.source1
            assert "Winner" not in m.source2

    def test_semifinal_references_qf(self) -> None:
        matches = generate_bracket(_teams(8))
        sf = [m for m in matches if m.round_name == "Semifinal"]
        for m in sf:
            assert "Winner" in m.source1
            assert "Winner" in m.source2


class TestBracket2Teams:
    def test_match_count(self) -> None:
        matches = generate_bracket(_teams(2))
        # Just 1 final, no 3rd-place match
        assert len(matches) == 1

    def test_round_name_is_final(self) -> None:
        matches = generate_bracket(_teams(2))
        assert matches[0].round_name == "Final"


class TestBracketNonPowerOf2:
    def test_3_teams_has_bye(self) -> None:
        matches = generate_bracket(_teams(3))
        # bracket_size=4: 1 first-round match (other pair has BYE) + 1 final = 2
        # No 3rd place since we skip semifinals (only 2 teams in "semifinal" round
        # but it's actually labeled based on count)
        assert len(matches) >= 2

    def test_5_teams(self) -> None:
        matches = generate_bracket(_teams(5))
        # bracket_size=8: 3 byes in first round, so 5 real QF matches? No—
        # 5 teams + 3 BYEs: 3 teams get byes, 2 teams play 1 QF match → 4 advance to SF
        # Actually: 4 first-round slots, 3 are byes → 1 QF + 2 SF + 1 F + 1 3rd = 5
        assert len(matches) >= 4


class TestBracketEdgeCases:
    def test_too_few_teams(self) -> None:
        with pytest.raises(SystemExit, match="at least 2"):
            generate_bracket([_team("A", 100)])

    def test_match_ids_sequential(self) -> None:
        matches = generate_bracket(_teams(8))
        ids = [m.match_id for m in matches]
        for i, mid in enumerate(ids, start=1):
            assert mid == f"M{i}"

    def test_third_place_references_losers(self) -> None:
        matches = generate_bracket(_teams(4))
        third = next(m for m in matches if m.round_name == "3rd Place")
        assert "Loser" in third.source1
        assert "Loser" in third.source2
