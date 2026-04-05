"""Tests for LLM output validation."""

from app.security.output_validator import compute_quality_score, validate_sop


def test_validate_empty_content():
    is_valid, issues = validate_sop("")
    assert not is_valid
    assert "empty" in issues[0].lower()


def test_validate_too_short():
    short = " ".join(["word"] * 100)
    is_valid, issues = validate_sop(short)
    assert not is_valid
    assert any("Too short" in i for i in issues)


def test_validate_too_long():
    long = " ".join(["word"] * 1000)
    is_valid, issues = validate_sop(long)
    assert not is_valid
    assert any("Too long" in i for i in issues)


def test_validate_good_content():
    content = " ".join(["word"] * 600)
    is_valid, issues = validate_sop(content)
    assert is_valid
    assert len(issues) == 0


def test_validate_generic_phrases():
    content = (
        "I am passionate about computer science. From a young age I knew this was my dream university. "
        "Throughout my academic journey I have been committed. " + " ".join(["word"] * 550)
    )
    _is_valid, issues = validate_sop(content)
    assert any("generic" in i.lower() for i in issues)


def test_validate_prompt_leakage():
    content = "As an AI, I cannot complete this request. " + " ".join(["word"] * 550)
    _is_valid, issues = validate_sop(content)
    assert any("leakage" in i.lower() for i in issues)


def test_compute_quality_score_good():
    content = " ".join(["word"] * 600)
    score = compute_quality_score(content)
    assert 0.0 <= score <= 1.0
    assert score >= 0.7


def test_compute_quality_score_penalised():
    content = "I am passionate about my dream university. From a young age I knew. " + " ".join(["word"] * 100)
    score = compute_quality_score(content)
    assert score < 1.0


def test_validate_regex_generic_phrase():
    filler = " ".join(["word"] * 550)
    content = (
        f"{filler} I am passionate about science. From a young age I studied. "
        "Throughout my academic journey I improved. This was a deeply passionate transformative experience."
    )
    _ok, issues = validate_sop(content)
    assert any("generic" in i.lower() for i in issues)


def test_validate_sop_relevance_penalises_compute_score():
    content = " ".join(["word"] * 600)
    with_ref = compute_quality_score(content, target_program={"university_name": "word"})
    no_ref = compute_quality_score(content, target_program={"university_name": "OtherUniversity"})
    assert with_ref >= no_ref
