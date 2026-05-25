# Security Policy

## Scope
ModelMirror runs locally and is designed for offline operation.

## Reporting
Report vulnerabilities privately to project maintainers. Include:
- Impact summary
- Reproduction steps
- Affected files/versions

## Security expectations

- No telemetry or network runtime calls.
- No execution of arbitrary tools from UI inputs.
- Validate all bundle and tool-args JSON inputs.
- Treat malformed inputs as fail-closed.
- Do not commit real prompt bundles if they contain private user data, secrets, privileged instructions, or proprietary context.
- Prefer sanitized examples under `templates/` and `examples/`.
