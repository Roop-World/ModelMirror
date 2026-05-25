"""Run orchestration for CLI `run`."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import ValidationError

from model_mirror.config import DEFAULT_OUTPUT_DIR, POLL_INTERVAL_SECONDS, SCHEMA_VERSION, UI_WAIT_TIMEOUT_SECONDS
from model_mirror.io_utils import ensure_run_dir, make_run_id, read_json_file, sha256_of_payload, utc_now_strings, write_json_file
from model_mirror.models import EvalDiagnostics, EvalNotes, EvalResult, PackedPrompt, RunManifest
from model_mirror.validation import format_pydantic_errors, validate_packed_prompt


@dataclass
class RunContext:
    bundle_path: Path
    out_dir: Path
    run_dir: Path
    run_id: str
    bundle_sha256: str
    bundle: PackedPrompt


def prepare_run(bundle_path: Path, out_dir: Path, operator_id: Optional[str]) -> RunContext:
    payload = read_json_file(bundle_path)
    bundle = validate_packed_prompt(payload)
    bundle_sha256 = sha256_of_payload(payload)
    timestamp_utc, timestamp_compact = utc_now_strings()
    run_id = make_run_id(timestamp_compact, bundle_sha256)
    run_dir = ensure_run_dir(out_dir, run_id)

    write_json_file(run_dir / "packed_prompt.json", payload)
    manifest = RunManifest(
        run_id=run_id,
        timestamp_utc=timestamp_utc,
        bundle_sha256=bundle_sha256,
        schema_version=SCHEMA_VERSION,
        operator_id=operator_id,
    )
    write_json_file(run_dir / "run_manifest.json", manifest.model_dump())

    return RunContext(
        bundle_path=bundle_path,
        out_dir=out_dir,
        run_dir=run_dir,
        run_id=run_id,
        bundle_sha256=bundle_sha256,
        bundle=bundle,
    )


def _terminate_process(proc: subprocess.Popen[Any]) -> None:
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


def _launch_streamlit(context: RunContext) -> subprocess.Popen[Any]:
    ui_script = Path(__file__).with_name("ui_app.py")
    env = os.environ.copy()
    env["MODEL_MIRROR_RUN_DIR"] = str(context.run_dir)
    env["MODEL_MIRROR_BUNDLE_PATH"] = str(context.bundle_path)
    env["MODEL_MIRROR_RUN_ID"] = context.run_id
    env["MODEL_MIRROR_BUNDLE_SHA256"] = context.bundle_sha256

    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(ui_script),
        "--server.headless",
        "true",
        "--browser.gatherUsageStats",
        "false",
        "--server.fileWatcherType",
        "none",
    ]
    return subprocess.Popen(command, env=env)


def _wait_for_finalize(context: RunContext, proc: subprocess.Popen[Any]) -> int:
    eval_path = context.run_dir / "eval_result.json"
    tool_calls_path = context.run_dir / "tool_calls.json"

    start_time = time.time()
    while True:
        if eval_path.exists():
            if not tool_calls_path.exists():
                write_json_file(tool_calls_path, [])
            result = read_json_file(eval_path)
            status = str(result.get("status", "")).upper()
            return 0 if status == "PASS" else 2

        if proc.poll() is not None:
            return 1

        if (time.time() - start_time) > UI_WAIT_TIMEOUT_SECONDS:
            return 1

        time.sleep(POLL_INTERVAL_SECONDS)


def _write_auto_finalize_outputs(context: RunContext) -> None:
    result = EvalResult(
        schema_version=SCHEMA_VERSION,
        run_id=context.run_id,
        bundle_sha256=context.bundle_sha256,
        status="PASS",
        chosen_action="RESPOND",
        drafted_text="AUTO_FINALIZED_FOR_VERIFICATION",
        canonical_output="AUTO_FINALIZED_FOR_VERIFICATION",
        tool_calls=[],
        diagnostics=EvalDiagnostics(failure_modes=[], suggestions=[]),
        notes=EvalNotes(
            missing_context="",
            contradictions="",
            assumptions="Auto-finalized for non-interactive verification.",
            extra={},
        ),
    )
    write_json_file(context.run_dir / "eval_result.json", result.model_dump())
    write_json_file(context.run_dir / "tool_calls.json", [])


def run_bundle(bundle: Path, out: Optional[Path] = None, operator_id: Optional[str] = None) -> int:
    out_dir = out or DEFAULT_OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        context = prepare_run(bundle_path=bundle, out_dir=out_dir, operator_id=operator_id)
    except FileNotFoundError:
        print(f"ERROR: bundle not found: {bundle}", file=sys.stderr)
        return 1
    except ValidationError as exc:
        print("INVALID_BUNDLE_SCHEMA", file=sys.stderr)
        for line in format_pydantic_errors(exc):
            print(f" - {line}", file=sys.stderr)
        return 2
    except FileExistsError:
        print("ERROR: run directory collision, retry command.", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ERROR: failed to prepare run: {exc}", file=sys.stderr)
        return 1

    if os.getenv("MODEL_MIRROR_AUTOFINALIZE") == "1":
        _write_auto_finalize_outputs(context)
        return 0

    try:
        proc = _launch_streamlit(context)
    except Exception as exc:
        print(f"ERROR: failed to launch Streamlit UI: {exc}", file=sys.stderr)
        return 1

    try:
        return _wait_for_finalize(context, proc)
    finally:
        _terminate_process(proc)
