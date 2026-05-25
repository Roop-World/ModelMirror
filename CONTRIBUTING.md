# Contributing

## Development setup
1. Install Python 3.10+.
2. Install package in editable mode:
   - `python3 -m pip install -e .`
3. Install development dependencies:
   - `python3 -m pip install -e ".[dev]"`
4. Run checks:
   - `python3 -m pytest`

## Contribution guidelines
- Keep runtime offline-only.
- Do not add telemetry or network calls.
- Never execute real tools from ModelMirror; only record intended calls.
- Do not commit captured production prompts, secrets, user data, or vendor credentials.
- Keep schema changes backwards-conscious and documented in `TECH_SPECS.md`.
- Keep scope small and deterministic.

## Pull request expectations
- Include tests for behavior changes.
- Update docs/templates/examples when schemas or CLI behavior changes.
- Provide before/after notes for artifact changes.
