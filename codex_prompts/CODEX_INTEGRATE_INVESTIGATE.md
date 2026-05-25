# CODEX_INTEGRATE_INVESTIGATE

Investigate a repository and produce an integration patch plan for ModelMirror.

## Investigation checklist
1. Find where messages/prompts are composed.
2. Find where tools and schemas are defined.
3. Find retrieval/context assembly points.
4. Identify runtime constraint source (`max_output_tokens`, model name, etc.).
5. Determine safest hook for `--dump-pack`.
6. Determine gate insertion point before model/tool execution.

## Deliverable
Produce:
- exact files/functions to modify
- data mapping table to ModelMirror schema
- command integration snippet for CI and local dev
- artifact retention path recommendation

## Rule
Do not execute real tools while debugging ModelMirror integration.
