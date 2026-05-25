# ModelMirror — Project Specification

## Purpose
ModelMirror is a local, human-in-the-loop prompt-pack debugger for agent systems.

Instead of discovering packing/tooling failures only after model inference, ModelMirror loads the packed bundle, lets a human emulate the model action (respond, tool-call, clarify, refuse), enforces JSON compliance via UI-assisted inputs, and writes deterministic artifacts for gating workflows.

## Why this exists
Rapid agent development often drifts prompt contracts, tool schemas, and retrieval context. ModelMirror provides a deterministic pre-inference check to catch those issues before execution.

## Scope (V1)
- Offline-only runtime; no telemetry; no network calls.
- Framework-agnostic packed prompt input with passthrough `raw` payload.
- Streamlit no-code/low-code harness for human model emulation.
- Deterministic run artifacts suitable for CI/manual gate checks.
- Structural pack diff CLI.
- Failure-mode logging with “Possible mitigations (not guaranteed fixes)”.

## Non-goals (V1)
- No real tool execution.
- No LLM calls for conversion/scoring.
- No accounts/auth/database.
- No plugin system.
- No cloud/multi-user/project-management features.
- No semantic/AI diff analysis.

## Primary Users
- Solo builders and small teams building agent workflows quickly.
- Engineers using code-generation assistants who need a manual quality gate.
- Teams requiring auditable PASS/FAIL artifacts for prompt-pack changes.

## Core Concepts
### Packed Prompt Bundle
Single JSON object containing conversation prompts, retrieved snippets, tool schemas, runtime constraints, and passthrough framework-native payload.

### Human Model Actions
- `RESPOND`
- `TOOL_CALL`
- `CLARIFY`
- `REFUSE`

### Compliance-first UI
Humans can write free text, but tool calls are constructed with explicit tool selector + JSON args editor + validation. Canonical envelope is deterministic:

```json
{"action":"tool_call","tool_name":"X","args":{}}
```

### Deterministic Audit Trail
Each run creates a timestamp/hash-based folder with copied bundle and machine-readable outputs.

## V1 User Stories
1. Load any packed bundle and inspect system/developer/user prompts, context, tools, and runtime constraints.
2. Emulate model behavior in UI and create validated tool-call envelope without executing tools.
3. Detect known failure modes and review mitigation suggestions.
4. Finalize PASS/FAIL with structured notes and store deterministic artifacts.
5. Diff two bundles structurally to identify prompt/tool/context/runtime drift.

## Acceptance Criteria
- `python -m model_mirror run --bundle <file>` launches UI and writes required artifacts on finalize.
- `doctor` validates bundle and fails closed on schema errors.
- `diff` reports grouped structural changes and optional JSON output.
- No runtime network calls or telemetry.
- No real tool execution under any action mode.
