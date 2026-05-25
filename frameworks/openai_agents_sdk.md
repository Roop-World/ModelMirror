# ModelMirror Integration: OpenAI Agents SDK

## Where to dump a packed prompt
Capture data at the point where agent messages, tool definitions, and context are prepared before model invocation. Write `packed_prompt.json` using ModelMirror schema.

## How to run ModelMirror
```bash
python3 -m model_mirror doctor --bundle packed_prompt.json
python3 -m model_mirror run --bundle packed_prompt.json --out outputs --operator openai_agents_sdk
```

## Gate execution on PASS/FAIL
- If `doctor` exits non-zero: stop.
- After `run`, read `outputs/<run_id>/eval_result.json`.
- Continue agent execution only if `status == "PASS"`.

## Artifacts to store
- `packed_prompt.json`
- `run_manifest.json`
- `eval_result.json`
- `tool_calls.json`
