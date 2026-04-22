"""Script to push eval_results.json to the eval-history branch."""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Push eval results to eval-history branch")
    parser.add_argument("--dry-run", action="store_true", help="Print steps but do not push")
    args = parser.parse_args()

    eval_file = Path("eval_results.json")
    if not eval_file.exists():
        print("Warning: eval_results.json not found. Exiting.")
        sys.exit(0)

    try:
        with open(eval_file, "r") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading eval_results.json: {e}")
        sys.exit(0)

    avg_score = data.get("avg_score", 0.0)
    commit_sha = os.getenv("GITHUB_SHA") or "unknown_sha"
    repo = os.getenv("GITHUB_REPOSITORY")
    token = os.getenv("GITHUB_TOKEN")

    if not args.dry_run and not token:
        print("Warning: GITHUB_TOKEN not set. Cannot push history. Exiting.")
        sys.exit(0)

    if not args.dry_run and not repo:
        print("Warning: GITHUB_REPOSITORY not set. Cannot push history. Exiting.")
        sys.exit(0)

    remote_url = f"https://x-access-token:{token}@github.com/{repo}.git" if token else "mock_url"

    # Use a temporary directory to clone the branch
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Cloning eval-history branch into temp dir {temp_dir}...")

        # Try to clone the eval-history branch
        clone_cmd = ["git", "clone", "--branch", "eval-history", "--depth", "1", remote_url, temp_dir]

        if args.dry_run:
            print(f"DRY RUN: Would run: {' '.join(clone_cmd).replace(token or 'TOKEN', '***')}")
            # Mock the clone by creating the directory structure
            os.makedirs(os.path.join(temp_dir, "history"), exist_ok=True)
            has_branch = True
        else:
            result = subprocess.run(clone_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print("Branch eval-history not found or cannot clone. Creating new orphan branch.")
                has_branch = False

                # Initialize new repo in temp_dir
                subprocess.run(["git", "init"], cwd=temp_dir, check=True)
                subprocess.run(["git", "checkout", "--orphan", "eval-history"], cwd=temp_dir, check=True)
            else:
                has_branch = True

        history_dir = os.path.join(temp_dir, "history")
        os.makedirs(history_dir, exist_ok=True)

        # Copy file
        dest_file = os.path.join(history_dir, f"{commit_sha}.json")
        print(f"Copying eval_results.json to {dest_file}")
        shutil.copy2(eval_file, dest_file)

        if args.dry_run:
            print(f"DRY RUN: Would add, commit, and push {dest_file} to eval-history branch")
            print(f"DRY RUN: Commit message: 'eval: {commit_sha} score={avg_score}'")
            print("DRY RUN completed successfully.")
            sys.exit(0)

        # Add, commit, push
        # Configure git user if running in Actions
        subprocess.run(["git", "config", "user.name", "github-actions[bot]"], cwd=temp_dir, check=True)
        subprocess.run(
            ["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"], cwd=temp_dir, check=True
        )

        subprocess.run(["git", "add", f"history/{commit_sha}.json"], cwd=temp_dir, check=True)

        # Check if there are changes to commit
        status_res = subprocess.run(["git", "status", "--porcelain"], cwd=temp_dir, capture_output=True, text=True)
        if not status_res.stdout.strip():
            print("No changes to commit. Exiting.")
            sys.exit(0)

        commit_msg = f"eval: {commit_sha} score={avg_score}"
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=temp_dir, check=True)

        print("Pushing to eval-history branch...")
        if has_branch:
            subprocess.run(["git", "push", "origin", "eval-history"], cwd=temp_dir, check=True)
        else:
            subprocess.run(["git", "remote", "add", "origin", remote_url], cwd=temp_dir, check=True)
            subprocess.run(["git", "push", "-u", "origin", "eval-history"], cwd=temp_dir, check=True)

        print("eval_results.json successfully pushed to eval-history branch.")


if __name__ == "__main__":
    main()
