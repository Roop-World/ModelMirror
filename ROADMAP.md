# ModelMirror Roadmap

ModelMirror starts as a small offline prompt-pack debugger. The long-term direction is a broader agent testing harness, but the core should stay portable and deterministic.

## V1: Prompt-Pack Debugger

- Load a packed prompt bundle.
- Let a human emulate model behavior.
- Validate bundle and tool-call structure.
- Produce deterministic PASS/FAIL artifacts.
- Diff prompt packs structurally.

## V2: Runtime Expectation Harness

- Capture the runtime activity a human expects from an LLM.
- Compare expected behavior against the actual prompt pack and tool contract.
- Help decide whether the prompt, context builder, tool schema, or harness should change.
- Keep real tool execution behind explicit adapters, never inside the default debugger path.

## Future Adapters

- Framework-specific pack exporters.
- Optional CI gates.
- Optional runtime trace import.
- Optional human-review dashboards.

Non-goals remain important: no hidden telemetry, no default network calls, no secret capture, and no automatic legal, medical, financial, or safety-critical judgment.
