# ModelMirror — Technical Specification

## Runtime and Packaging
- Python 3.10+
- Source package: `src/model_mirror/`
- Dependencies: `streamlit`, `pydantic`, `jsonschema`
- CLI via `python -m model_mirror ...`
- Offline/local runtime only

## CLI

### Run
`python -m model_mirror run --bundle <packed_prompt.json> [--out outputs] [--operator <id>]`

Flow:
1. Load JSON bundle.
2. Validate against PackedPrompt schema.
3. Compute SHA256 on canonical JSON.
4. Create run dir: `outputs/<YYYYMMDDTHHMMSSZ__hashprefix>`.
5. Write `packed_prompt.json` copy and `run_manifest.json`.
6. Launch Streamlit UI scoped to this run context.
7. Wait for `eval_result.json` and `tool_calls.json`.
8. Exit `0` on PASS, `2` on FAIL, `1` on error/aborted.

Optional non-interactive verification mode:
- If `MODEL_MIRROR_AUTOFINALIZE=1` is set, `run` writes deterministic PASS artifacts directly and exits `0` (for CI/local smoke tests).

### Doctor
`python -m model_mirror doctor --bundle <packed_prompt.json>`

- Validates bundle schema.
- Reports lint diagnostics (including ambiguous tool schemas).
- Exit `0` valid, `2` invalid/fail-closed findings, `1` operational error.

### Diff
`python -m model_mirror diff --a <A.json> --b <B.json> [--out <path>]`

- Structural deterministic diff only.
- Terminal summary always printed.
- Optional JSON report written to `--out`.

## Input Schema: PackedPrompt (`schema_version=1.0`)

```json
{
  "schema_version": "1.0",
  "conversation": {
    "system": "string",
    "developer": "string (optional)",
    "user": "string"
  },
  "context": {
    "retrieved_snippets": [
      {
        "id": "string",
        "source": "string",
        "text": "string",
        "metadata": {}
      }
    ]
  },
  "tools": [
    {
      "name": "string",
      "description": "string",
      "json_schema": {}
    }
  ],
  "runtime": {
    "mode": "agent",
    "constraints": {
      "max_output_tokens": 1024,
      "model_name": "string"
    }
  },
  "raw": {}
}
```

Validation behavior:
- Fail-closed for malformed schema/types.
- Allow empty arrays where reasonable (`tools`, `retrieved_snippets`).
- Root extras forbidden; framework extras must go in `raw`.

## Output Schemas

### `run_manifest.json`
- `run_id`
- `timestamp_utc`
- `bundle_sha256`
- `schema_version`
- `operator_id` (optional)

### `tool_calls.json`
- Array of intended calls only: `[{"tool_name":"...","args":{...}}]`
- May be empty.
- Never executed.

### `eval_result.json`
- `schema_version`
- `run_id`
- `bundle_sha256`
- `status`: `PASS|FAIL`
- `chosen_action`: `RESPOND|TOOL_CALL|CLARIFY|REFUSE`
- `drafted_text`
- `canonical_output`: string or canonical tool envelope
- `tool_calls`
- `diagnostics`:
  - `failure_modes`: `{code,severity,message,evidence}`[]
  - `suggestions`: suggestion entries from library
- `notes`: `missing_context`, `contradictions`, `assumptions`, `extra`

## Determinism Rules
- Canonical JSON for hashing:
  - `json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)`
- `run_id = <timestamp_utc_compact>__<sha256_prefix12>`
- Artifact files written with stable key order + trailing newline.

## Streamlit UI Spec (V1)

### Left pane
- Conversation: system/developer/user.
- Context snippets list with metadata.
- Tools list with schemas.
- Runtime constraints.

### Right pane
- Action selector: `RESPOND`, `TOOL_CALL`, `CLARIFY`, `REFUSE`.
- Free-text draft box always available.
- Tool-call mode:
  - Tool dropdown
  - JSON args editor (separate from free text)
  - Validation against selected tool `json_schema` when possible
  - `Wrap into canonical envelope` button
- Finalize section:
  - PASS/FAIL selector
  - notes fields
  - finalize writes `eval_result.json` + `tool_calls.json`.

## Failure Modes (minimum required)
- `INVALID_BUNDLE_SCHEMA`
- `INVALID_JSON_OUTPUT`
- `JSON_TRUNCATION_RISK`
- `PROSE_JSON_MIX`
- `TOOL_SCHEMA_AMBIGUOUS`
- `MISSING_CONTEXT`
- `CONTRADICTORY_INSTRUCTIONS`

### Truncation heuristic
If `runtime.constraints.max_output_tokens` exists:
- `char_budget = max_output_tokens * 4`
- If `len(canonical_json_output) > char_budget`:
  - add `JSON_TRUNCATION_RISK`
  - default status to `FAIL`
  - surface suggestions.

## Suggestions Library
File: `suggestions/suggestion_library.json`

Entry shape:
```json
{
  "id": "string",
  "applies_to": ["FAILURE_CODE"],
  "title": "string",
  "lines": ["copy-ready mitigation line"],
  "confidence": "HIGH|MED|LOW",
  "rationale": "string"
}
```

## Diff Spec (deterministic, no semantics)
Grouped output sections:
- System/developer/user text unified diffs.
- Tools added/removed.
- Same-name tool schema changed (pretty old/new + unified diff).
- Retrieved snippet IDs or text hashes added/removed.
- Runtime constraints changed.
- Bundle fingerprints (A/B SHA256).
