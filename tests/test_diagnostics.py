from model_mirror.diagnostics import build_finalize_failure_modes, check_truncation_risk
from model_mirror.validation import validate_packed_prompt


def _bundle(max_tokens=10):
    return validate_packed_prompt(
        {
            "schema_version": "1.0",
            "conversation": {"system": "s", "developer": "d", "user": "u"},
            "context": {"retrieved_snippets": []},
            "tools": [{"name": "t", "description": "", "json_schema": {"type": "object"}}],
            "runtime": {"mode": "agent", "constraints": {"max_output_tokens": max_tokens}},
            "raw": {},
        }
    )


def test_truncation_risk_detected():
    has_risk, budget, actual = check_truncation_risk({"max_output_tokens": 1}, {"k": "x" * 20})
    assert has_risk is True
    assert budget == 4
    assert actual > budget


def test_finalize_failure_modes_contains_expected_codes():
    bundle = _bundle(max_tokens=1)
    failures, trunc = build_finalize_failure_modes(
        bundle=bundle,
        chosen_action="TOOL_CALL",
        drafted_text="please call tool",
        canonical_output={"action": "tool_call", "tool_name": "t", "args": {"x": "y" * 20}},
        selected_tool=bundle.tools[0],
        args_parse_error="bad json",
        args_schema_error="TOOL_SCHEMA_AMBIGUOUS",
        missing_context="missing doc",
        contradictions="prompt conflict",
    )
    codes = {f.code for f in failures}
    assert "INVALID_JSON_OUTPUT" in codes
    assert "TOOL_SCHEMA_AMBIGUOUS" in codes
    assert "PROSE_JSON_MIX" in codes
    assert "MISSING_CONTEXT" in codes
    assert "CONTRADICTORY_INSTRUCTIONS" in codes
    assert "JSON_TRUNCATION_RISK" in codes
    assert trunc is True
