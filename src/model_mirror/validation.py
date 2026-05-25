"""Validation and linting helpers."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from jsonschema import ValidationError as JsonSchemaValidationError
from jsonschema import validate as jsonschema_validate
from pydantic import ValidationError

from model_mirror.models import FailureMode, PackedPrompt


def validate_packed_prompt(bundle_payload: Dict[str, Any]) -> PackedPrompt:
    return PackedPrompt.model_validate(bundle_payload)


def format_pydantic_errors(exc: ValidationError) -> List[str]:
    messages: List[str] = []
    for err in exc.errors():
        loc = ".".join(str(part) for part in err.get("loc", []))
        msg = err.get("msg", "validation error")
        messages.append(f"{loc}: {msg}" if loc else msg)
    return messages


def lint_tool_schema_ambiguity(bundle: PackedPrompt) -> List[FailureMode]:
    findings: List[FailureMode] = []
    for idx, tool in enumerate(bundle.tools):
        if not isinstance(tool.json_schema, dict) or not tool.json_schema:
            findings.append(
                FailureMode(
                    code="TOOL_SCHEMA_AMBIGUOUS",
                    severity="MED",
                    message="Tool schema is missing or empty.",
                    evidence={"tool_name": tool.name, "tool_index": idx},
                )
            )
    return findings


def validate_tool_args(args_payload: Dict[str, Any], tool_schema: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    if not isinstance(tool_schema, dict) or not tool_schema:
        return False, "TOOL_SCHEMA_AMBIGUOUS"

    try:
        jsonschema_validate(instance=args_payload, schema=tool_schema)
    except JsonSchemaValidationError as exc:
        return False, str(exc)
    except Exception as exc:  # invalid schema or other local validation issue
        return False, f"TOOL_SCHEMA_AMBIGUOUS: {exc}"
    return True, None
