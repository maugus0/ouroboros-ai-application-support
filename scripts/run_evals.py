"""LLM Evaluation Runner for CI/CD."""

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# Ensure app is importable
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# flake8: noqa: E402
from app.llm.openai_client import call_openai
from app.llm.prompts import get_cover_letter_prompt, get_sop_outline_prompt


def get_prompt_for_operation(operation: str, context: Dict[str, Any]) -> str:
    """Gets the appropriate system prompt for the given operation."""
    if operation == "sop_generate":
        # We test the outline generation step as the primary indicator for SOP quality
        return get_sop_outline_prompt(context=context, fmt="text")
    elif operation == "cover_letter_generate":
        return get_cover_letter_prompt(context=context, fmt="text")
    else:
        raise ValueError(f"Unknown operation: {operation}")


async def generate_response(operation: str, context: Dict[str, Any], dry_run: bool) -> str:
    """Generates a response from the LLM based on the input context."""
    if dry_run:
        await asyncio.sleep(0.5)
        return '{"draft": "This is a mock response from the LLM."}'

    system_prompt = get_prompt_for_operation(operation, context)
    user_content = json.dumps(context, indent=2)

    try:
        raw_response = await call_openai(
            user_content=user_content,
            system_prompt=system_prompt,
            max_tokens=4000,
            response_format=None,  # Output is usually text or specific json, we evaluate as text
        )
        return raw_response.get("content", "")
    except Exception as e:
        print(f"Error calling OpenAI for generation: {e}")
        return ""


async def judge_output(
    input_context: Dict[str, Any], output_text: str, rubric: str, criteria: str, dry_run: bool
) -> Dict[str, Any]:
    """Uses GPT-4o-mini to evaluate the generated output."""
    if dry_run:
        await asyncio.sleep(0.5)
        return {"score": 7.5, "reason": "Dry run mock evaluation."}

    judge_system_prompt = (
        "You are an expert evaluator assessing the quality of AI-generated documents. "
        "You will be provided with the user's INPUT context, the generated OUTPUT, and the EVALUATION CRITERIA. "
        "Score the output strictly according to the provided RUBRIC. "
        "Respond ONLY with a valid JSON object in this exact format: "
        '{"score": <float>, "reason": "<brief justification>"}'
    )

    judge_user_prompt = f"""
### RUBRIC ###
{rubric}

### CRITERIA ###
{criteria}

### INPUT CONTEXT ###
{json.dumps(input_context, indent=2)}

### GENERATED OUTPUT ###
{output_text}
"""

    for attempt in range(2):
        try:
            raw_response = await call_openai(
                user_content=judge_user_prompt,
                system_prompt=judge_system_prompt,
                model_override="gpt-4o-mini",
                max_tokens=500,
                response_format="json",
            )
            content_str = raw_response.get("content", "{}")
            result = json.loads(content_str)
            if "score" not in result:
                raise ValueError("JSON response missing 'score' field.")
            return {"score": float(result["score"]), "reason": result.get("reason", "No reason provided.")}
        except Exception as e:
            print(f"Judge attempt {attempt + 1} failed: {e}")
            if attempt == 1:
                return {"score": 0.0, "reason": f"Judge failed: {str(e)}"}
            await asyncio.sleep(1)

    return {"score": 0.0, "reason": "Judge failed all attempts."}


async def run_evals(dry_run: bool):
    """Main evaluation runner."""
    fixtures_dir = ROOT_DIR / "tests" / "llm" / "fixtures"

    # Load golden cases
    try:
        with open(fixtures_dir / "sop_golden_cases.json", "r") as f:
            sop_cases = json.load(f)
        with open(fixtures_dir / "cover_letter_golden.json", "r") as f:
            cl_cases = json.load(f)
    except FileNotFoundError as e:
        print(f"Error loading fixtures: {e}")
        sys.exit(1)

    all_cases = sop_cases + cl_cases

    # Load rubric
    try:
        with open(fixtures_dir / "judge_rubric.json", "r") as f:
            rubric_dict = json.load(f)
    except FileNotFoundError as e:
        print(f"Error loading rubric: {e}")
        sys.exit(1)

    baseline_score_str = os.getenv("EVAL_BASELINE_SCORE", "0.0")
    try:
        baseline_score = float(baseline_score_str)
    except ValueError:
        baseline_score = 0.0

    print(f"Starting evaluations (Dry run: {dry_run}). Total cases: {len(all_cases)}")
    print(f"Target Baseline Score: {baseline_score}")
    print("-" * 50)

    results = []
    total_score = 0.0

    for i, case in enumerate(all_cases):
        print(f"Evaluating [{i+1}/{len(all_cases)}] {case['id']}...")
        start_time = time.perf_counter()

        # Generate response
        generated_output = await generate_response(case["operation"], case["input"], dry_run)

        if not generated_output:
            print(f"  -> Generation failed for {case['id']}")
            score = 0.0
            reason = "Generation failed or returned empty output."
        else:
            # Get specific rubric based on operation
            op_rubric = rubric_dict.get(case["operation"], {}).get("rubric", "Score 1-10.")

            # Judge response
            judge_res = await judge_output(
                case["input"], generated_output, op_rubric, case.get("evaluation_criteria", ""), dry_run
            )
            score = judge_res.get("score", 0.0)
            reason = judge_res.get("reason", "")

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        print(f"  -> Score: {score}/10.0 (Latency: {latency_ms}ms)")
        print(f"  -> Reason: {reason}")

        results.append(
            {
                "id": case["id"],
                "score": score,
                "reason": reason,
                "latency_ms": latency_ms,
                "operation": case["operation"],
            }
        )
        total_score += score

    avg_score = total_score / len(all_cases) if all_cases else 0.0
    passed = avg_score >= (baseline_score - 0.5)

    print("-" * 50)
    print(f"Evaluation Complete!")
    print(f"Average Score: {avg_score:.2f} (Baseline: {baseline_score:.2f})")
    print(f"Result: {'PASS' if passed else 'FAIL'}")

    report = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "commit_sha": os.getenv("GITHUB_SHA", "unknown"),
        "avg_score": round(avg_score, 2),
        "baseline_score": baseline_score,
        "passed": passed,
        "cases": results,
    }

    with open("eval_results.json", "w") as f:
        json.dump(report, f, indent=2)
    print("Report saved to eval_results.json")

    if not passed:
        print("FAIL: Average score dropped more than 0.5 points below baseline.")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run LLM Evaluations")
    parser.add_argument("--dry-run", action="store_true", help="Run without calling actual LLM APIs")
    args = parser.parse_args()

    if not args.dry_run and not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable is required when not using --dry-run.")
        sys.exit(1)

    asyncio.run(run_evals(args.dry_run))
