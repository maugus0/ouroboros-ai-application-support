"""PII Guard Script to detect potential PII in fixture files."""

import argparse
import os
import re
import sys
from typing import Dict, List, Tuple

# Patterns to detect PII
PATTERNS: Dict[str, re.Pattern] = {
    "Email": re.compile(r"\b[\w.+-]+@(?:gmail|yahoo|hotmail|outlook|icloud)\.com\b", re.IGNORECASE),
    "VN Phone": re.compile(r"(\+84|0[3-9])\d{8,9}\b"),
    "US Phone": re.compile(r"\+1[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "VN CCCD/CMND": re.compile(r"\b\d{9}\b|\b\d{12}\b"),
    "US SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
}


def scan_file(file_path: str) -> Tuple[List[Tuple[int, str]], List[str]]:
    """Scans a single file for PII patterns. Returns findings and any read/decode errors."""
    findings: List[Tuple[int, str]] = []
    errors: List[str] = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                for pattern_name, pattern in PATTERNS.items():
                    if pattern.search(line):
                        findings.append((line_num, pattern_name))
    except (OSError, UnicodeDecodeError) as e:
        errors.append(f"Error reading {file_path}: {e}")
    return findings, errors


def scan_path(path: str) -> Tuple[List[Tuple[str, int, str]], List[str]]:
    """Scans a file or directory for PII patterns."""
    all_findings: List[Tuple[str, int, str]] = []
    read_errors: List[str] = []
    if os.path.isfile(path):
        file_findings, file_errors = scan_file(path)
        read_errors.extend(file_errors)
        for line_num, pattern_name in file_findings:
            all_findings.append((path, line_num, pattern_name))
    elif os.path.isdir(path):
        for root, _, files in os.walk(path):
            for file in files:
                if not file.endswith(".json"):  # Only scan JSON fixtures for now
                    continue
                file_path = os.path.join(root, file)
                file_findings, file_errors = scan_file(file_path)
                read_errors.extend(file_errors)
                for line_num, pattern_name in file_findings:
                    all_findings.append((file_path, line_num, pattern_name))
    else:
        print(f"Error: Path not found: {path}")
        sys.exit(1)
    return all_findings, read_errors


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Scan files for PII")
    parser.add_argument("--path", required=True, help="File or directory to scan")
    parser.add_argument("--warn-only", action="store_true", help="Print warnings but do not exit with error")
    args = parser.parse_args()

    findings, read_errors = scan_path(args.path)

    if read_errors:
        for error in read_errors:
            print(error, file=sys.stderr)
        if not args.warn_only:
            print("\nError: One or more files could not be read. Failing safe to avoid missing PII.", file=sys.stderr)
            sys.exit(1)

    if not findings:
        if read_errors and args.warn_only:
            print(f"PII Guard: Scan completed with unreadable files in {args.path}; exiting with 0 due to --warn-only.")
        else:
            print(f"PII Guard: No PII found in {args.path}")
        sys.exit(0)

    print("⚠️  PII Guard Findings:")
    for file_path, line_num, pattern_name in findings:
        print(f"  - {file_path}:{line_num} -> Found possible {pattern_name} [REDACTED]")

    if args.warn_only:
        print("\nWarnings printed, exiting with 0 due to --warn-only.")
        sys.exit(0)
    else:
        print("\nError: PII found! Please remove real data from fixtures.")
        sys.exit(1)


if __name__ == "__main__":
    main()
