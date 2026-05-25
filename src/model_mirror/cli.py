"""Command-line entrypoint for ModelMirror."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from pydantic import ValidationError

from model_mirror.diffing import compute_diff_report, render_diff_summary
from model_mirror.io_utils import read_json_file, write_json_file
from model_mirror.run_flow import run_bundle
from model_mirror.validation import format_pydantic_errors, lint_tool_schema_ambiguity, validate_packed_prompt


def _cmd_run(args: argparse.Namespace) -> int:
    return run_bundle(bundle=Path(args.bundle), out=Path(args.out) if args.out else None, operator_id=args.operator)


def _cmd_doctor(args: argparse.Namespace) -> int:
    bundle_path = Path(args.bundle)
    try:
        payload = read_json_file(bundle_path)
    except FileNotFoundError:
        print(f"ERROR: bundle not found: {bundle_path}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ERROR: failed to read bundle: {exc}", file=sys.stderr)
        return 1

    try:
        bundle = validate_packed_prompt(payload)
    except ValidationError as exc:
        print("INVALID_BUNDLE_SCHEMA")
        for line in format_pydantic_errors(exc):
            print(f" - {line}")
        return 2

    findings = lint_tool_schema_ambiguity(bundle)
    if findings:
        print("Doctor findings:")
        for item in findings:
            print(f" - {item.code}: {item.message} :: {item.evidence}")
        return 2

    print("Doctor: PASS (bundle schema is valid; no ambiguity findings)")
    return 0


def _cmd_diff(args: argparse.Namespace) -> int:
    try:
        bundle_a = read_json_file(Path(args.a))
        bundle_b = read_json_file(Path(args.b))
    except FileNotFoundError as exc:
        print(f"ERROR: file not found: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ERROR: failed to read diff inputs: {exc}", file=sys.stderr)
        return 1

    report = compute_diff_report(bundle_a, bundle_b)
    print(render_diff_summary(report))

    if args.out:
        write_json_file(Path(args.out), report)
        print(f"\nWrote diff report: {args.out}")

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="model_mirror", description="ModelMirror CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    run_parser = sub.add_parser("run", help="Launch human prompt-pack debugger UI")
    run_parser.add_argument("--bundle", required=True, help="Path to packed prompt JSON")
    run_parser.add_argument("--out", default="outputs", help="Output directory")
    run_parser.add_argument("--operator", default=None, help="Optional operator ID")
    run_parser.set_defaults(func=_cmd_run)

    doctor_parser = sub.add_parser("doctor", help="Validate a packed prompt bundle")
    doctor_parser.add_argument("--bundle", required=True, help="Path to packed prompt JSON")
    doctor_parser.set_defaults(func=_cmd_doctor)

    diff_parser = sub.add_parser("diff", help="Diff two packed prompt bundles")
    diff_parser.add_argument("--a", required=True, help="Bundle A JSON path")
    diff_parser.add_argument("--b", required=True, help="Bundle B JSON path")
    diff_parser.add_argument("--out", default=None, help="Optional JSON output report path")
    diff_parser.set_defaults(func=_cmd_diff)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
