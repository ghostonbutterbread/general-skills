from pathlib import Path


SKILL = Path(__file__).resolve().parents[1] / "skills" / "script_manager" / "SKILL.md"


def test_deterministic_scripts_have_bounded_authority() -> None:
    text = SKILL.read_text(encoding="utf-8")

    assert "Deterministic Mechanics, Bounded Authority" in text
    assert "exhaustive: false" in text
    assert "zero matches" in text.lower()
    assert "observed facts" in text.lower()
    assert "seed signals" in text.lower()
    assert "unknowns" in text.lower()


def test_script_learning_requires_evidence_and_review() -> None:
    text = " ".join(SKILL.read_text(encoding="utf-8").lower().split())

    assert "failing fixture or test" in text
    assert "generalized implementation" in text
    assert "false positives" in text
    assert "review" in text
