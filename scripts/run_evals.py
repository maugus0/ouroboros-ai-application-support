"""LLM Evaluation Runner for CI/CD."""

import argparse
import asyncio
import hashlib
import json
import os
import statistics
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


def compute_prompt_version(prompts_dir: Path) -> str:
    """Computes a deterministic version from the prompt template files."""
    if not prompts_dir.exists() or not prompts_dir.is_dir():
        return "unknown"
    digest = hashlib.sha256()
    try:
        # Recursively find all JSON prompt templates
        for prompt_file in sorted(prompts_dir.rglob("*.json")):
            if not prompt_file.is_file():
                continue
            # Include relative path in hash to detect moves/renames
            digest.update(str(prompt_file.relative_to(prompts_dir)).encode("utf-8"))
            digest.update(b"\0")
            digest.update(prompt_file.read_bytes())
            digest.update(b"\0")
    except Exception:
        return "unknown"
    return digest.hexdigest()[:12]


def get_prompt_for_operation(operation: str, context: Dict[str, Any]) -> str:
    """Gets the appropriate system prompt for the given operation."""
    if operation == "sop_generate":
        # We test the outline generation step as the primary indicator for SOP quality
        return get_sop_outline_prompt(context=context, fmt="text")
    elif operation == "cover_letter_generate":
        return get_cover_letter_prompt(context=context, fmt="text")
    else:
        raise ValueError(f"Unknown operation: {operation}")


async def generate_response(operation: str, context: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    """Generates a response from the LLM based on the input context."""
    if dry_run:
        await asyncio.sleep(0.5)
        return {
            "content": '{"draft": "This is a mock response from the LLM."}',
            "model": "gpt-4o-mock",
            "input_tokens": 100,
            "output_tokens": 200,
            "temperature": 0.7,
        }

    system_prompt = get_prompt_for_operation(operation, context)
    user_content = json.dumps(context, indent=2)

    try:
        raw_response = await call_openai(
            prompt=user_content,
            system_message=system_prompt,
            max_tokens=4000,
            temperature=0.7,
            response_format=None,  # Output is usually text or specific json, we evaluate as text
        )
        return raw_response
    except Exception as e:
        print(f"Error calling OpenAI for generation: {e}")
        return {"content": "", "model": "unknown", "input_tokens": 0, "output_tokens": 0, "temperature": 0.7}


async def judge_output(
    input_context: Dict[str, Any],
    output_text: str,
    rubric: str,
    criteria: str,
    dry_run: bool,
    model_override: str = "gpt-4o-mini",
) -> Dict[str, Any]:
    """Uses GPT-4o-mini to evaluate the generated output."""
    if dry_run:
        await asyncio.sleep(0.5)
        return {"score": 7.5, "reason": "Dry run mock evaluation.", "model": "gpt-4o-mini-mock"}

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
                prompt=judge_user_prompt,
                system_message=judge_system_prompt,
                model=model_override,
                max_tokens=500,
                temperature=0.7,
                response_format="json",
            )
            content_str = raw_response.get("content", "{}")
            result = json.loads(content_str)
            if "score" not in result:
                raise ValueError("JSON response missing 'score' field.")
            return {
                "score": float(result["score"]),
                "reason": result.get("reason", "No reason provided."),
                "model": raw_response.get("model", "gpt-4o-mini"),
            }
        except Exception as e:
            print(f"Judge attempt {attempt + 1} failed: {e}")
            if attempt == 1:
                return {"score": 0.0, "reason": f"Judge failed: {str(e)}"}
            await asyncio.sleep(1)

    return {"score": 0.0, "reason": "Judge failed all attempts.", "model": "unknown"}


async def run_evals(dry_run: bool):
    """Main evaluation runner."""
    fixtures_dir = ROOT_DIR / "tests" / "llm" / "fixtures"
    prompts_dir = ROOT_DIR / "prompts"

    # Get prompt version from the actual prompt template source of truth
    prompt_version = compute_prompt_version(prompts_dir)

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

    bias_threshold = float(os.getenv("BIAS_THRESHOLD", "1.5"))
    bias_hard_limit = float(os.getenv("BIAS_HARD_LIMIT", "3.0"))

    print(f"Starting evaluations (Dry run: {dry_run}). Total cases: {len(all_cases)}")
    print(f"Target Baseline Score: {baseline_score}")
    print(f"Bias Threshold: {bias_threshold}, Hard Limit: {bias_hard_limit}")
    print("-" * 50)

    results = []
    total_score = 0.0

    for i, case in enumerate(all_cases):
        print(f"Evaluating [{i+1}/{len(all_cases)}] {case['id']}...")
        start_time = time.perf_counter()

        # Generate response
        generated_res = await generate_response(case["operation"], case["input"], dry_run)
        generated_output = generated_res.get("content", "")

        if not generated_output:
            print(f"  -> Generation failed for {case['id']}")
            score = 0.0
            reason = "Generation failed or returned empty output."
            model_id = "unknown"
            judge_model_id = "unknown"
            token_usage = {"prompt_tokens": 0, "completion_tokens": 0}
            temperature = 0.7
        else:
            # Get specific rubric based on operation
            op_rubric = rubric_dict.get(case["operation"], {}).get("rubric", "Score 1-10.")

            # Judge response
            judge_res = await judge_output(
                case["input"], generated_output, op_rubric, case.get("evaluation_criteria", ""), dry_run
            )
            score = judge_res.get("score", 0.0)
            reason = judge_res.get("reason", "")

            model_id = generated_res.get("model", "unknown")
            judge_model_id = judge_res.get("model", "unknown")
            token_usage = {
                "prompt_tokens": generated_res.get("input_tokens", 0),
                "completion_tokens": generated_res.get("output_tokens", 0),
            }
            temperature = generated_res.get("temperature", 0.7)

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        print(f"  -> Score: {score}/10.0 (Latency: {latency_ms}ms, Model: {model_id})")
        print(f"  -> Reason: {reason}")

        results.append(
            {
                "id": case["id"],
                "score": score,
                "reason": reason,
                "latency_ms": latency_ms,
                "operation": case["operation"],
                "prompt_version": prompt_version,
                "temperature": temperature,
                "token_usage": token_usage,
                "model_id": model_id,
                "judge_model_id": judge_model_id,
            }
        )
        total_score += score

    # Bias Evaluation
    print("\n" + "=" * 50)
    print("Starting Bias Detection Evaluations...")
    bias_report = {"max_bias_gap": 0.0, "bias_threshold": bias_threshold, "hard_limit": bias_hard_limit, "cases": []}
    has_hard_fail = False

    for case in all_cases:
        variants = case.get("demographic_variants", [])
        if not variants:
            continue

        print(f"\nBias testing for {case['id']} ({len(variants)} variants)...")
        variant_scores = []
        tested_names = []
        op_rubric = rubric_dict.get(case["operation"], {}).get("rubric", "Score 1-10.")

        for idx, variant in enumerate(variants):
            if dry_run:
                v_score = 7.0 if idx == 0 else 7.5
                v_reason = "Mock bias variant."
            else:
                # Merge variant into input
                v_input = case["input"].copy()
                v_input.update(variant)
                v_res = await generate_response(case["operation"], v_input, dry_run)
                v_out = v_res.get("content", "")
                v_judge = await judge_output(v_input, v_out, op_rubric, case.get("evaluation_criteria", ""), dry_run)
                v_score = v_judge.get("score", 0.0)
                v_reason = v_judge.get("reason", "")

            variant_scores.append(v_score)
            tested_names.append(variant.get("student_name") or variant.get("applicant_name") or f"Variant {idx}")
            print(f"  - {tested_names[-1]}: {v_score}/10")

        bias_gap = round(max(variant_scores) - min(variant_scores), 2)
        if bias_gap > bias_report["max_bias_gap"]:
            bias_report["max_bias_gap"] = bias_gap

        status = "ok"
        if bias_gap > bias_hard_limit:
            status = "hard_fail"
            has_hard_fail = True
            print(f"  -> ❌ HARD FAIL: Bias gap {bias_gap} exceeds limit {bias_hard_limit}!")
        elif bias_gap > bias_threshold:
            status = "warning"
            print(f"  -> ⚠️ WARNING: Bias gap {bias_gap} exceeds threshold {bias_threshold}.")
        else:
            print(f"  -> ✅ OK: Bias gap {bias_gap}.")

        bias_report["cases"].append(
            {
                "case_id": case["id"],
                "variants_tested": tested_names,
                "scores": variant_scores,
                "bias_gap": bias_gap,
                "status": status,
            }
        )

    # Calculate latencies
    latencies = sorted([r["latency_ms"] for r in results])
    if latencies:
        latency_p50_ms = int(statistics.median(latencies))
        if len(latencies) >= 2:
            # Use statistics.quantiles (Python 3.8+) for consistent percentile calculation
            # method='inclusive' matches the standard P95 definition for small samples
            q = statistics.quantiles(latencies, n=100, method="inclusive")
            latency_p95_ms = int(q[94])  # q is 0-indexed, so q[94] is the 95th percentile
        else:
            latency_p95_ms = latencies[0]
    else:
        latency_p50_ms = 0
        latency_p95_ms = 0

    global_model_id = results[0]["model_id"] if results else "unknown"
    global_judge_model_id = results[0]["judge_model_id"] if results else "unknown"

    avg_score = total_score / len(all_cases) if all_cases else 0.0
    passed = avg_score >= (baseline_score - 0.5)

    print("-" * 50)
    print(f"Evaluation Complete!")
    print(f"Average Score: {avg_score:.2f} (Baseline: {baseline_score:.2f})")
    print(f"Latency P50: {latency_p50_ms}ms, P95: {latency_p95_ms}ms")
    print(f"Result: {'PASS' if passed else 'FAIL'}")

    report = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "commit_sha": os.getenv("GITHUB_SHA", "unknown"),
        "model_id": global_model_id,
        "judge_model_id": global_judge_model_id,
        "latency_p50_ms": latency_p50_ms,
        "latency_p95_ms": latency_p95_ms,
        "avg_score": round(avg_score, 2),
        "baseline_score": baseline_score,
        "passed": passed,
        "bias_report": bias_report,
        "cases": results,
    }

    with open("eval_results.json", "w") as f:
        json.dump(report, f, indent=2)
    print("Report saved to eval_results.json")

    if not passed:
        print("FAIL: Average score dropped more than 0.5 points below baseline.")
        sys.exit(1)

    if has_hard_fail:
        print(f"FAIL: Bias gap exceeded hard limit of {bias_hard_limit} in at least one case.")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run LLM Evaluations")
    parser.add_argument("--dry-run", action="store_true", help="Run without calling actual LLM APIs")
    args = parser.parse_args()

    if not args.dry_run and not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable is required when not using --dry-run.")
        sys.exit(1)

    asyncio.run(run_evals(args.dry_run))
