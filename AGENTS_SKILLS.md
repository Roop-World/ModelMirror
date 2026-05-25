# AGENTS_SKILLS.md

## ModelMirror Integration Recipe (for coding agents)

Use this when wiring ModelMirror into any agent framework.

### Literal checklist
- [ ] Find where your agent builds messages/tools/context.
- [ ] Write `packed_prompt.json` in ModelMirror schema.
- [ ] Run ModelMirror (`doctor`, then `run`).
- [ ] If FAIL, stop and fix the pack before agent execution.
- [ ] Store artifacts (`run_manifest.json`, `eval_result.json`, `tool_calls.json`, bundle copy).

## Minimal wiring contract

### 1) Locate pack assembly point
Find the code path that constructs:
- system/developer/user prompt text
- retrieved context snippets
- available tools + arg schema
- runtime constraints

### 2) Emit ModelMirror bundle
Create JSON file with fields:
- `schema_version`
- `conversation`
- `context.retrieved_snippets`
- `tools`
- `runtime.mode`, `runtime.constraints`
- `raw` passthrough for framework-native payload

### 3) Gate execution with ModelMirror
Recommended gate sequence:
1. `python -m model_mirror doctor --bundle packed_prompt.json`
2. `python -m model_mirror run --bundle packed_prompt.json --out outputs --operator <id>`
3. Read `eval_result.json` status
4. Continue agent execution only on PASS

### 4) Persist audit artifacts
Store per run:
- packed input bundle
- run manifest
- eval result
- intended tool calls

## Framework-agnostic pseudocode

```python
pack = build_framework_pack(...)
model_mirror_pack = map_to_model_mirror(pack)
write_json("packed_prompt.json", model_mirror_pack)

if run_cmd("python -m model_mirror doctor --bundle packed_prompt.json") != 0:
    raise RuntimeError("Prompt pack invalid")

rc = run_cmd("python -m model_mirror run --bundle packed_prompt.json --out outputs --operator ci")
if rc != 0:
    raise RuntimeError("Human gate failed")

eval_result = read_json(latest_run_dir / "eval_result.json")
if eval_result["status"] != "PASS":
    raise RuntimeError("ModelMirror FAIL gate")

# safe to execute actual agent runtime after this point
```

## Enforcement notes
- Never execute tools inside ModelMirror.
- Treat FAIL as hard stop in CI unless explicitly waived.
- Keep mapping logic thin; place framework-specific extras in `raw`.
