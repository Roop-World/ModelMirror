# CODEX_INTEGRATE_OPERATE

You are integrating ModelMirror into an existing agent repository.

## Required actions
1. Add `--dump-pack <path>` support where the agent prepares model input.
2. Add `--human-eval` mode that runs ModelMirror before real execution.
3. Emit ModelMirror bundle schema (`schema_version`, `conversation`, `context`, `tools`, `runtime`, `raw`).
4. Run:
   - `python -m model_mirror doctor --bundle <dumped_pack.json>`
   - `python -m model_mirror run --bundle <dumped_pack.json> --out outputs --operator <repo_name>`
5. Gate execution:
   - If doctor fails or eval status is FAIL, stop pipeline.
6. Persist artifacts:
   - `packed_prompt.json`, `run_manifest.json`, `eval_result.json`, `tool_calls.json`.

## Constraints
- No telemetry.
- No network calls added by ModelMirror integration.
- Never execute tool calls during ModelMirror phase.
