# ModelMirror

[![Tests](https://github.com/Roop-World/ModelMirror/actions/workflows/tests.yml/badge.svg)](https://github.com/Roop-World/ModelMirror/actions/workflows/tests.yml)

ModelMirror is an offline human prompt-pack debugger for agent workflows.

Project page: https://roopsdevassist.com/modelmirror/

It lets a human step into the model's seat before an LLM call happens. Load the exact prompt bundle your agent runtime would send, inspect the messages, tools, retrieved context, and constraints, then emulate what the model should do: `RESPOND`, `TOOL_CALL`, `CLARIFY`, or `REFUSE`.

ModelMirror validates the bundle, records structured PASS/FAIL artifacts, and helps teams tighten expectations before changing either the prompt pack or the harness that produced it.

## Features

- Local-only Streamlit UI harness.
- Human model-emulation flow for response, tool-call, clarification, and refusal behavior.
- Deterministic run artifacts for manual gates and CI smoke checks.
- Fail-closed bundle validation with `doctor`.
- Structural prompt-pack diffing with `diff`.
- Suggestions library for common failure modes.
- No telemetry, no network runtime calls, no real tool execution.

## Why This Exists

Agent failures often start before inference: missing context, ambiguous tool schemas, conflicting instructions, malformed JSON expectations, or unrealistic runtime constraints. ModelMirror gives builders a cheap preflight loop for those failures.

Use it when you want to answer questions like:

- What exactly did our agent send to the model?
- Would a reasonable human know which tool to call?
- Is the tool-call envelope clear and valid?
- Did a prompt or retrieval change alter the expected behavior?
- Should we adjust the prompt pack, the runtime harness, or both?

## Install

```bash
python3 -m pip install -e .
```

If your shell uses `python` instead of `python3`, commands are equivalent.

## Quickstart

### 1) Validate bundle

```bash
python3 -m model_mirror doctor --bundle templates/packed_prompt.example.json
```

### 2) Run human debugger UI

```bash
python3 -m model_mirror run --bundle templates/packed_prompt.example.json --out outputs --operator demo_operator
```

On finalize, artifacts are written to:

```text
outputs/<run_id>/
```

For non-interactive verification/CI only:

```bash
MODEL_MIRROR_AUTOFINALIZE=1 python3 -m model_mirror run --bundle templates/packed_prompt.example.json --out outputs --operator ci
```

### 3) Diff packs

```bash
python3 -m model_mirror diff \
  --a templates/packed_prompt.minimal.json \
  --b templates/packed_prompt.example.json
```

Optional JSON report:

```bash
python3 -m model_mirror diff --a A.json --b B.json --out pack_diff_report.json
```

## Run artifacts

Each run writes:

- `packed_prompt.json`
- `run_manifest.json`
- `eval_result.json`
- `tool_calls.json`

`run_id` format: `YYYYMMDDTHHMMSSZ__<hashprefix>`

## ModelMirror input schema (minimal)

```json
{
  "schema_version": "1.0",
  "conversation": {"system": "...", "developer": "...", "user": "..."},
  "context": {"retrieved_snippets": []},
  "tools": [],
  "runtime": {"mode": "agent", "constraints": {}},
  "raw": {}
}
```

## Integration docs

- Framework guides: `frameworks/`
- Agent wiring guide: `AGENTS_SKILLS.md`
- Codex integration prompts: `codex_prompts/`

## Current Scope

ModelMirror V1 is intentionally narrow:

- It does not call an LLM.
- It does not execute tools.
- It does not score model quality automatically.
- It does not run a cloud service, store accounts, or maintain a database.

The job is to make prompt-pack expectations visible and testable before runtime.

## Roadmap

The natural next step is an integrated agent runtime testing harness: humans should be able to test the runtime activities they expect from an LLM, compare those expectations against the actual harness behavior, and decide whether to change the prompt pack, the tool contract, or the harness itself.

That future layer should remain compatible with ModelMirror's core rule: the base debugger stays local, deterministic, and non-executing unless a caller explicitly opts into a separate runtime adapter.

See `ROADMAP.md` for the current release path.

## Releases

See `CHANGELOG.md` for release notes.

## Security and privacy

- No telemetry.
- No network calls in runtime flow.
- ModelMirror never executes tools; it records intended tool calls only.

## License
Apache-2.0 (`LICENSE`).
