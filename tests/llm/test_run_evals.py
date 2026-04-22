"""LLMOps tests for the eval runner contract and deterministic judge behavior."""

import pytest

from scripts import run_evals


def test_dry_run_bias_scores_default_to_passing_gap(monkeypatch):
    monkeypatch.delenv("EVAL_DRY_RUN_BIAS_SCORES", raising=False)

    assert run_evals.get_dry_run_bias_score(0) == 7.0
    assert run_evals.get_dry_run_bias_score(1) == 7.5
    assert run_evals.get_dry_run_bias_score(2) == 7.5


def test_dry_run_bias_scores_can_exercise_warning_or_hard_fail_gap(monkeypatch):
    monkeypatch.setenv("EVAL_DRY_RUN_BIAS_SCORES", "6.0, 9.5")

    assert run_evals.get_dry_run_bias_score(0) == 6.0
    assert run_evals.get_dry_run_bias_score(1) == 9.5
    assert run_evals.get_dry_run_bias_score(2) == 9.5


@pytest.mark.parametrize(
    ("bias_gap", "expected_status", "expected_hard_fail"),
    [
        (0.5, "ok", False),
        (2.0, "warning", False),
        (3.5, "hard_fail", True),
    ],
)
def test_classify_bias_gap_covers_ok_warning_and_hard_fail(
    bias_gap: float,
    expected_status: str,
    expected_hard_fail: bool,
):
    status, hard_fail = run_evals.classify_bias_gap(
        bias_gap,
        bias_threshold=1.5,
        bias_hard_limit=3.0,
    )

    assert status == expected_status
    assert hard_fail is expected_hard_fail


@pytest.mark.asyncio
async def test_judge_output_uses_deterministic_temperature(monkeypatch):
    captured_kwargs = {}

    async def fake_call_openai(**kwargs):
        captured_kwargs.update(kwargs)
        return {
            "content": '{"score": 8.25, "reason": "Looks good."}',
            "model": "judge-model",
            "input_tokens": 10,
            "output_tokens": 5,
            "total_tokens": 15,
        }

    monkeypatch.setattr(run_evals, "call_openai", fake_call_openai)

    result = await run_evals.judge_output(
        input_context={"student_name": "Jane Example"},
        output_text="Generated application content.",
        rubric="Score 1-10.",
        criteria="Prefer specific evidence.",
        dry_run=False,
    )

    assert captured_kwargs["temperature"] == run_evals.JUDGE_TEMPERATURE == 0.0
    assert captured_kwargs["model"] == "gpt-4o-mini"
    assert result == {"score": 8.25, "reason": "Looks good.", "model": "judge-model"}


@pytest.mark.asyncio
async def test_generate_response_uses_call_openai_flat_return_contract(monkeypatch):
    async def fake_call_openai(**_kwargs):
        return {
            "content": "Generated SOP draft.",
            "model": "generation-model",
            "input_tokens": 100,
            "output_tokens": 200,
            "total_tokens": 300,
        }

    monkeypatch.setattr(run_evals, "call_openai", fake_call_openai)
    monkeypatch.setattr(run_evals, "get_prompt_for_operation", lambda *_args, **_kwargs: "system prompt")

    result = await run_evals.generate_response(
        operation="sop_generate",
        context={"student_name": "Jane Example"},
        dry_run=False,
    )

    assert result == {
        "content": "Generated SOP draft.",
        "model": "generation-model",
        "input_tokens": 100,
        "output_tokens": 200,
        "total_tokens": 300,
    }
