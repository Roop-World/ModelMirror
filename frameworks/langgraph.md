# ModelMirror Integration: LangGraph

## Where to dump a packed prompt
Before the LLM node call, serialize the graph state pieces used to create the model request into ModelMirror schema and save `packed_prompt.json`.

## How to run ModelMirror
```bash
python3 -m model_mirror doctor --bundle packed_prompt.json
python3 -m model_mirror run --bundle packed_prompt.json --out outputs --operator langgraph
```

## Gate execution on PASS/FAIL
- Fail-fast on `doctor != 0`.
- Block graph execution if ModelMirror `run` returns `2` or if `eval_result.json` status is `FAIL`.

## Artifacts to store
Store generated run artifacts with build IDs/commit SHA for regression investigation.
