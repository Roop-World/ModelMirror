# ModelMirror Integration: Google ADK

## Where to dump a packed prompt
At the adapter layer where ADK composes prompt instructions, tool contracts, and retrieval context, emit a ModelMirror-compatible `packed_prompt.json`.

## How to run ModelMirror
```bash
python3 -m model_mirror doctor --bundle packed_prompt.json
python3 -m model_mirror run --bundle packed_prompt.json --out outputs --operator google_adk
```

## Gate execution on PASS/FAIL
- Treat non-zero `doctor` as blocking.
- Treat `run` exit code `2` as gate failure.
- Optional: parse `eval_result.json` and enforce `status == "PASS"`.

## Artifacts to store
Persist the run directory contents for traceability and release audit.
