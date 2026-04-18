"""Updates the GitHub repository variable with the new evaluation baseline score."""

import argparse
import json
import os
import subprocess
import sys


def update_baseline(dry_run: bool):
    """Reads eval_results.json and updates the EVAL_BASELINE_SCORE via gh CLI."""
    if not os.path.exists("eval_results.json"):
        print("Error: eval_results.json not found. Run evaluations first.")
        sys.exit(1)

    try:
        with open("eval_results.json", "r") as f:
            results = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error parsing eval_results.json: {e}")
        sys.exit(1)

    if "avg_score" not in results:
        print("Error: eval_results.json is missing 'avg_score'.")
        sys.exit(1)

    new_score = results["avg_score"]
    old_score = results.get("baseline_score", 0.0)

    print(f"Current baseline: {old_score}")
    print(f"New score: {new_score}")

    if not os.getenv("GITHUB_TOKEN") and not dry_run:
        print("Warning: GITHUB_TOKEN is not set. Cannot update baseline.")
        print("Exiting without error.")
        sys.exit(0)

    repo = os.getenv("GITHUB_REPOSITORY")
    if not repo and not dry_run:
        print("Warning: GITHUB_REPOSITORY is not set. Cannot update baseline.")
        sys.exit(0)

    if dry_run:
        print(f"[DRY RUN] Would update GitHub variable EVAL_BASELINE_SCORE to {new_score} for {repo}")
        return

    try:
        print(f"Updating EVAL_BASELINE_SCORE to {new_score} for {repo}...")
        cmd = ["gh", "variable", "set", "EVAL_BASELINE_SCORE", "--body", str(new_score), "--repo", repo]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("Baseline updated successfully.")
        if result.stdout:
            print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Failed to update GitHub variable. Error:\n{e.stderr}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Store new LLM evaluation baseline score")
    parser.add_argument("--dry-run", action="store_true", help="Print what would happen without making changes")
    args = parser.parse_args()

    update_baseline(args.dry_run)
