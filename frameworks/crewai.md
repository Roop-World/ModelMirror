# ModelMirror Integration: CrewAI

## Where to dump a packed prompt
In the task execution path where role prompts, context, and tool interfaces are packaged for model use, write `packed_prompt.json` in ModelMirror format.

## How to run ModelMirror
```bash
python3 -m model_mirror doctor --bundle packed_prompt.json
python3 -m model_mirror run --bundle packed_prompt.json --out outputs --operator crewai
```

## Gate execution on PASS/FAIL
- Stop execution on non-zero `doctor`.
- Run proceeds only when ModelMirror final `status` is `PASS`.

## Artifacts to store
Keep the run folder (`manifest`, `eval_result`, `tool_calls`, bundle copy) under your CI/job artifacts.
