"""Failure-mode generation and deterministic checks."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from model_mirror.io_utils import canonical_json
from model_mirror.models import FailureMode, PackedPrompt, ToolDefinition

SEVERITY_DEFAULTS = {
    "INVALID_BUNDLE_SCHEMA": "HIGH",
    "INVALID_JSON_OUTPUT": "HIGH",
    "JSON_TRUNCATION_RISK": "HIGH",
    "PROSE_JSON_MIX": "MED",
    "TOOL_SCHEMA_AMBIGUOUS": "MED",
    "MISSING_CONTEXT": "MED",
    "CONTRADICTORY_INSTRUCTIONS": "MED",
}


def build_failure(code: str, message: str, evidence: Optional[Dict[str, Any]] = None) -> FailureMode:
    return FailureMode(
        code=code,
        severity=SEVERITY_DEFAULTS.get(code, "LOW"),
        message=message,
        evidence=evidence,
    )


def serialize_canonical_output(canonical_output: Any) -> str:
    if isinstance(canonical_output, (dict, list)):
        return canonical_json(canonical_output)
    return json.dumps(str(canonical_output), ensure_ascii=False)


def check_truncation_risk(constraints: Dict[str, Any], canonical_output: Any) -> Tuple[bool, Optional[int], int]:
    raw_max_tokens = constraints.get("max_output_tokens")
    if raw_max_tokens is None:
        return False, None, 0

    try:
        max_tokens = int(raw_max_tokens)
    except (TypeError, ValueError):
        return False, None, 0

    if max_tokens <= 0:
        return False, None, 0

    serialized = serialize_canonical_output(canonical_output)
    char_budget = max_tokens * 4
    actual_chars = len(serialized)
    return actual_chars > char_budget, char_budget, actual_chars


def detect_prose_json_mix(drafted_text: str) -> bool:
    stripped = drafted_text.strip()
    if not stripped:
        return False
    if (stripped.startswith("{") and stripped.endswith("}")) or (
        stripped.startswith("[") and stripped.endswith("]")
    ):
        return False
    return True


def build_finalize_failure_modes(
    bundle: PackedPrompt,
    chosen_action: str,
    drafted_text: str,
    canonical_output: Any,
    selected_tool: Optional[ToolDefinition],
    args_parse_error: Optional[str],
    args_schema_error: Optional[str],
    missing_context: str,
    contradictions: str,
) -> Tuple[List[FailureMode], bool]:
    failures: List[FailureMode] = []
    truncation_risk = False

    if args_parse_error:
        failures.append(
            build_failure(
                "INVALID_JSON_OUTPUT",
                "Tool args JSON could not be parsed.",
                evidence={"error": args_parse_error},
            )
        )

    if args_schema_error:
        if "TOOL_SCHEMA_AMBIGUOUS" in args_schema_error:
            failures.append(
                build_failure(
                    "TOOL_SCHEMA_AMBIGUOUS",
                    "Tool schema is ambiguous; arg validation is unreliable.",
                    evidence={"tool_name": getattr(selected_tool, "name", None), "error": args_schema_error},
                )
            )
        else:
            failures.append(
                build_failure(
                    "INVALID_JSON_OUTPUT",
                    "Tool args failed json_schema validation.",
                    evidence={"tool_name": getattr(selected_tool, "name", None), "error": args_schema_error},
                )
            )

    if chosen_action == "TOOL_CALL" and detect_prose_json_mix(drafted_text):
        failures.append(
            build_failure(
                "PROSE_JSON_MIX",
                "Draft text contains prose while tool-call JSON output is expected.",
            )
        )

    if missing_context.strip():
        failures.append(build_failure("MISSING_CONTEXT", "Operator marked missing context.", evidence={"note": missing_context}))

    if contradictions.strip():
        failures.append(
            build_failure(
                "CONTRADICTORY_INSTRUCTIONS",
                "Operator marked contradictory instructions.",
                evidence={"note": contradictions},
            )
        )

    has_risk, budget, actual = check_truncation_risk(bundle.runtime.constraints, canonical_output)
    if has_risk:
        truncation_risk = True
        failures.append(
            build_failure(
                "JSON_TRUNCATION_RISK",
                "Canonical output length exceeds heuristic character budget.",
                evidence={"char_budget": budget, "actual_chars": actual},
            )
        )

    return failures, truncation_risk
