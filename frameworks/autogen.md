# ModelMirror Integration: AutoGen

## Where to dump a packed prompt
At the point where AutoGen agent messages and tool schemas are assembled for the next turn, dump a ModelMirror `packed_prompt.json`.

## How to run ModelMirror
```bash
python3 -m model_mirror doctor --bundle packed_prompt.json
python3 -m model_mirror run --bundle packed_prompt.json --out outputs --operator autogen
```

## Gate execution on PASS/FAIL
- If `doctor` reports schema/ambiguity issues, stop.
- Require `eval_result.json.status == "PASS"` before allowing real agent/tool execution.

## Artifacts to store
Archive all four artifacts per gate run and associate with scenario/test case IDs.
