"""Streamlit UI for human prompt-pack debugging."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st
from pydantic import ValidationError

from model_mirror.diagnostics import build_finalize_failure_modes, check_truncation_risk
from model_mirror.io_utils import read_json_file, write_json_file
from model_mirror.models import EvalDiagnostics, EvalNotes, EvalResult, PackedPrompt, ToolCall
from model_mirror.suggestions import load_suggestion_library, suggestions_for_codes
from model_mirror.validation import validate_packed_prompt, validate_tool_args


def _env_required(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"Missing required env: {key}")
    return value


def _load_context() -> Tuple[Path, Path, str, str]:
    run_dir = Path(_env_required("MODEL_MIRROR_RUN_DIR"))
    bundle_path = Path(_env_required("MODEL_MIRROR_BUNDLE_PATH"))
    run_id = _env_required("MODEL_MIRROR_RUN_ID")
    bundle_sha256 = _env_required("MODEL_MIRROR_BUNDLE_SHA256")
    return run_dir, bundle_path, run_id, bundle_sha256


def _load_bundle(bundle_path: Path) -> PackedPrompt:
    payload = read_json_file(bundle_path)
    return validate_packed_prompt(payload)


def _init_state() -> None:
    defaults = {
        "chosen_action": "RESPOND",
        "drafted_text": "",
        "selected_tool_name": "",
        "tool_args_text": "{}",
        "wrapped_canonical": None,
        "wrapped_tool_name": None,
        "status_choice": "PASS",
        "truncation_default_applied": False,
        "finalized": False,
        "truncation_override": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _resolve_selected_tool(bundle: PackedPrompt) -> Optional[Any]:
    if not bundle.tools:
        return None
    current_name = st.session_state.get("selected_tool_name")
    if not current_name:
        return bundle.tools[0]
    for tool in bundle.tools:
        if tool.name == current_name:
            return tool
    return bundle.tools[0]


def _parse_args_json(args_text: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    try:
        payload = json.loads(args_text or "{}")
    except json.JSONDecodeError as exc:
        return None, str(exc)
    if not isinstance(payload, dict):
        return None, "Tool args JSON must decode to an object."
    return payload, None


def _candidate_canonical_output(bundle: PackedPrompt) -> Any:
    chosen_action = st.session_state.get("chosen_action", "RESPOND")
    drafted_text = st.session_state.get("drafted_text", "")
    if chosen_action != "TOOL_CALL":
        return drafted_text

    selected_tool = _resolve_selected_tool(bundle)
    if selected_tool is None:
        return drafted_text

    wrapped = st.session_state.get("wrapped_canonical")
    wrapped_name = st.session_state.get("wrapped_tool_name")
    if isinstance(wrapped, dict) and wrapped_name == selected_tool.name:
        return wrapped

    args_payload, parse_error = _parse_args_json(st.session_state.get("tool_args_text", "{}"))
    if parse_error:
        return drafted_text
    return {"action": "tool_call", "tool_name": selected_tool.name, "args": args_payload}


def _render_suggestions(codes: List[str]) -> None:
    library = load_suggestion_library()
    entries = suggestions_for_codes(codes, library)
    if not entries:
        return

    st.markdown("### Possible mitigations (not guaranteed fixes)")
    for entry in entries:
        st.markdown(f"**{entry.title}** ({entry.confidence})")
        for idx, line in enumerate(entry.lines):
            st.code(line, language="text")
        st.caption(entry.rationale)


def _write_outputs(
    run_dir: Path,
    run_id: str,
    bundle_sha256: str,
    chosen_action: str,
    drafted_text: str,
    canonical_output: Any,
    tool_calls: List[ToolCall],
    status: str,
    diagnostics: EvalDiagnostics,
    notes: EvalNotes,
) -> None:
    result = EvalResult(
        schema_version="1.0",
        run_id=run_id,
        bundle_sha256=bundle_sha256,
        status=status,
        chosen_action=chosen_action,  # type: ignore[arg-type]
        drafted_text=drafted_text,
        canonical_output=canonical_output,
        tool_calls=tool_calls,
        diagnostics=diagnostics,
        notes=notes,
    )
    write_json_file(run_dir / "eval_result.json", result.model_dump())
    write_json_file(run_dir / "tool_calls.json", [call.model_dump() for call in tool_calls])


def _auto_finalize_if_requested(run_dir: Path, run_id: str, bundle_sha256: str) -> bool:
    if os.getenv("MODEL_MIRROR_AUTOFINALIZE") != "1":
        return False
    if st.session_state.get("finalized"):
        return True

    diagnostics = EvalDiagnostics(failure_modes=[], suggestions=[])
    notes = EvalNotes(missing_context="", contradictions="", assumptions="Auto-finalized for non-interactive verification")
    _write_outputs(
        run_dir=run_dir,
        run_id=run_id,
        bundle_sha256=bundle_sha256,
        chosen_action="RESPOND",
        drafted_text="AUTO_FINALIZED_FOR_VERIFICATION",
        canonical_output="AUTO_FINALIZED_FOR_VERIFICATION",
        tool_calls=[],
        status="PASS",
        diagnostics=diagnostics,
        notes=notes,
    )
    st.session_state["finalized"] = True
    st.success("Auto-finalized run artifacts for verification.")
    return True


def main() -> None:
    st.set_page_config(page_title="ModelMirror", layout="wide")
    st.title("ModelMirror — Human Prompt-Pack Debugger")

    try:
        run_dir, bundle_path, run_id, bundle_sha256 = _load_context()
        bundle = _load_bundle(bundle_path)
    except ValidationError as exc:
        st.error("INVALID_BUNDLE_SCHEMA")
        st.code(str(exc))
        st.stop()
    except Exception as exc:
        st.error(str(exc))
        st.stop()

    _init_state()
    if _auto_finalize_if_requested(run_dir, run_id, bundle_sha256):
        return

    st.caption(f"Run ID: {run_id}")

    left, right = st.columns([1, 1], gap="large")

    with left:
        st.subheader("Packed Prompt")
        st.markdown("**System**")
        st.code(bundle.conversation.system, language="text")
        st.markdown("**Developer**")
        st.code(bundle.conversation.developer or "", language="text")
        st.markdown("**User**")
        st.code(bundle.conversation.user, language="text")

        st.markdown("**Retrieved Snippets**")
        if bundle.context.retrieved_snippets:
            for snippet in bundle.context.retrieved_snippets:
                with st.expander(f"{snippet.id} ({snippet.source})"):
                    st.code(snippet.text, language="text")
                    st.code(json.dumps(snippet.metadata, indent=2, sort_keys=True), language="json")
        else:
            st.info("No retrieved snippets.")

        st.markdown("**Tools**")
        if bundle.tools:
            for tool in bundle.tools:
                with st.expander(tool.name):
                    st.write(tool.description)
                    st.code(json.dumps(tool.json_schema, indent=2, sort_keys=True), language="json")
        else:
            st.info("No tools available in this bundle.")

        st.markdown("**Runtime Constraints**")
        st.code(json.dumps(bundle.runtime.constraints, indent=2, sort_keys=True), language="json")

    with right:
        st.subheader("Human Emulation")
        st.radio("Choose action", ["RESPOND", "TOOL_CALL", "CLARIFY", "REFUSE"], key="chosen_action", horizontal=True)

        st.text_area("Free-text draft (always recorded)", key="drafted_text", height=180)

        selected_tool = None
        args_parse_error: Optional[str] = None
        args_schema_error: Optional[str] = None

        if st.session_state["chosen_action"] == "TOOL_CALL":
            if not bundle.tools:
                st.warning("TOOL_CALL selected, but bundle.tools is empty.")
            else:
                tool_names = [tool.name for tool in bundle.tools]
                if st.session_state.get("selected_tool_name") not in tool_names:
                    st.session_state["selected_tool_name"] = tool_names[0]
                st.selectbox("Tool", tool_names, key="selected_tool_name")
                selected_tool = _resolve_selected_tool(bundle)

                st.text_area("Tool args JSON", key="tool_args_text", height=180)
                c1, c2 = st.columns(2)

                with c1:
                    if st.button("Validate args JSON"):
                        parsed_args, args_parse_error = _parse_args_json(st.session_state["tool_args_text"])
                        if args_parse_error:
                            st.error(f"INVALID_JSON_OUTPUT: {args_parse_error}")
                        else:
                            ok, err = validate_tool_args(parsed_args or {}, selected_tool.json_schema if selected_tool else {})
                            if ok:
                                st.success("Args JSON is valid for selected tool schema.")
                            else:
                                st.error(err or "INVALID_JSON_OUTPUT")

                with c2:
                    if st.button("Wrap into canonical envelope"):
                        parsed_args, args_parse_error = _parse_args_json(st.session_state["tool_args_text"])
                        if args_parse_error:
                            st.error(f"INVALID_JSON_OUTPUT: {args_parse_error}")
                        else:
                            ok, err = validate_tool_args(parsed_args or {}, selected_tool.json_schema if selected_tool else {})
                            args_schema_error = err
                            if not ok:
                                st.warning(err or "Args validation warning")
                            st.session_state["wrapped_canonical"] = {
                                "action": "tool_call",
                                "tool_name": selected_tool.name,
                                "args": parsed_args,
                            }
                            st.session_state["wrapped_tool_name"] = selected_tool.name
                            st.success("Canonical envelope generated.")

                wrapped = st.session_state.get("wrapped_canonical")
                wrapped_tool_name = st.session_state.get("wrapped_tool_name")
                if wrapped and selected_tool and wrapped_tool_name == selected_tool.name:
                    st.markdown("**Canonical Output Preview**")
                    st.code(json.dumps(wrapped, indent=2, sort_keys=True), language="json")

        candidate_output = _candidate_canonical_output(bundle)
        truncation_risk, char_budget, actual_chars = check_truncation_risk(bundle.runtime.constraints, candidate_output)
        if truncation_risk:
            st.warning(
                f"JSON_TRUNCATION_RISK: output has {actual_chars} chars, heuristic budget is {char_budget}. "
                "Default status will be FAIL."
            )
            if not st.session_state.get("truncation_default_applied", False):
                st.session_state["status_choice"] = "FAIL"
                st.session_state["truncation_default_applied"] = True
        else:
            st.session_state["truncation_default_applied"] = False
            st.session_state["truncation_override"] = False

        st.markdown("### Finalize")
        st.radio("PASS/FAIL", ["PASS", "FAIL"], key="status_choice", horizontal=True)
        st.text_area("notes.missing_context", key="note_missing_context", height=80)
        st.text_area("notes.contradictions", key="note_contradictions", height=80)
        st.text_area("notes.assumptions", key="note_assumptions", height=80)

        if truncation_risk and st.session_state["status_choice"] == "PASS":
            st.checkbox("Override truncation risk and keep PASS", key="truncation_override")

        if st.button("Finalize and Write Artifacts", type="primary"):
            chosen_action = st.session_state["chosen_action"]
            drafted_text = st.session_state["drafted_text"]
            canonical_output: Any = drafted_text
            tool_calls: List[ToolCall] = []

            if chosen_action == "TOOL_CALL":
                if not selected_tool:
                    args_parse_error = "No tool selected."
                    canonical_output = drafted_text
                else:
                    parsed_args, args_parse_error = _parse_args_json(st.session_state.get("tool_args_text", "{}"))
                    if args_parse_error:
                        canonical_output = {
                            "action": "tool_call",
                            "tool_name": selected_tool.name,
                            "args": {},
                        }
                    else:
                        ok, args_schema_error = validate_tool_args(parsed_args or {}, selected_tool.json_schema)
                        canonical_output = {
                            "action": "tool_call",
                            "tool_name": selected_tool.name,
                            "args": parsed_args,
                        }
                        tool_calls = [ToolCall(tool_name=selected_tool.name, args=parsed_args or {})]
                        if not ok and args_schema_error is None:
                            args_schema_error = "INVALID_JSON_OUTPUT"

            failure_modes, had_truncation_risk = build_finalize_failure_modes(
                bundle=bundle,
                chosen_action=chosen_action,
                drafted_text=drafted_text,
                canonical_output=canonical_output,
                selected_tool=selected_tool,
                args_parse_error=args_parse_error,
                args_schema_error=args_schema_error,
                missing_context=st.session_state.get("note_missing_context", ""),
                contradictions=st.session_state.get("note_contradictions", ""),
            )

            failure_codes = [mode.code for mode in failure_modes]
            suggestion_entries = suggestions_for_codes(failure_codes, load_suggestion_library())

            status = st.session_state["status_choice"]
            hard_fail = any(code in {"INVALID_JSON_OUTPUT", "TOOL_SCHEMA_AMBIGUOUS"} for code in failure_codes)
            if hard_fail:
                status = "FAIL"

            if had_truncation_risk and status == "PASS" and not st.session_state.get("truncation_override", False):
                status = "FAIL"

            notes = EvalNotes(
                missing_context=st.session_state.get("note_missing_context", ""),
                contradictions=st.session_state.get("note_contradictions", ""),
                assumptions=st.session_state.get("note_assumptions", ""),
                extra={},
            )

            diagnostics = EvalDiagnostics(failure_modes=failure_modes, suggestions=suggestion_entries)
            _write_outputs(
                run_dir=run_dir,
                run_id=run_id,
                bundle_sha256=bundle_sha256,
                chosen_action=chosen_action,
                drafted_text=drafted_text,
                canonical_output=canonical_output,
                tool_calls=tool_calls,
                status=status,
                diagnostics=diagnostics,
                notes=notes,
            )
            st.session_state["finalized"] = True
            st.success(f"Artifacts written to {run_dir}. You can close this tab.")

        failure_preview_codes: List[str] = []
        if truncation_risk:
            failure_preview_codes.append("JSON_TRUNCATION_RISK")
        if st.session_state.get("note_missing_context", "").strip():
            failure_preview_codes.append("MISSING_CONTEXT")
        if st.session_state.get("note_contradictions", "").strip():
            failure_preview_codes.append("CONTRADICTORY_INSTRUCTIONS")
        _render_suggestions(failure_preview_codes)


if __name__ == "__main__":
    main()
