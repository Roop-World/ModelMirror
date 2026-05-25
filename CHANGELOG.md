# Changelog

## v0.1.0 - 2026-05-25

Initial public release candidate.

### Added

- Offline Streamlit harness for human prompt-pack debugging.
- `doctor` command for fail-closed packed prompt validation.
- `diff` command for deterministic structural prompt-pack comparison.
- `run` command with deterministic run artifacts.
- `MODEL_MIRROR_AUTOFINALIZE=1` smoke path for CI and non-interactive verification.
- Example packed prompt templates and sample run artifacts.
- Framework integration notes for OpenAI Agents SDK, Google ADK, LangGraph, AutoGen, and CrewAI.
- Agent integration prompts for Codex-style coding agents.

### Security

- No telemetry.
- No default network calls in runtime flow.
- No real tool execution; ModelMirror records intended tool calls only.
