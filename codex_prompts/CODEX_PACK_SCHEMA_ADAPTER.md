# CODEX_PACK_SCHEMA_ADAPTER

Map an existing framework-specific prompt pack into ModelMirror schema.

## Adapter targets
Output JSON must contain:
- `schema_version: "1.0"`
- `conversation.system`, `conversation.developer` (optional), `conversation.user`
- `context.retrieved_snippets[]`
- `tools[]` with `name`, `description`, `json_schema`
- `runtime.mode`, `runtime.constraints`
- `raw` passthrough for untouched framework-native payload

## Mapping policy
- Keep mapping deterministic and local-only.
- Preserve unknown fields inside `raw` exactly.
- For missing optional blocks, use empty arrays/objects.
- Do not invent semantic transformations.

## Validation and gate
After mapping:
1. Write mapped JSON to `packed_prompt.json`.
2. Run `python -m model_mirror doctor --bundle packed_prompt.json`.
3. Fix all fail-closed issues before calling `run`.
