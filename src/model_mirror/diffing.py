"""Deterministic structural diffing for packed prompts."""

from __future__ import annotations

import difflib
import hashlib
import json
from typing import Any, Dict, List, Tuple

from model_mirror.io_utils import canonical_json


def _pretty_json(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)


def _unified_diff(old: str, new: str, old_name: str, new_name: str) -> List[str]:
    return list(
        difflib.unified_diff(
            old.splitlines(),
            new.splitlines(),
            fromfile=old_name,
            tofile=new_name,
            lineterm="",
        )
    )


def _bundle_sha(payload: Dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def _conversation_text(bundle: Dict[str, Any], role: str) -> str:
    return str(bundle.get("conversation", {}).get(role, ""))


def _tool_map(bundle: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for tool in bundle.get("tools", []) or []:
        if not isinstance(tool, dict):
            continue
        name = tool.get("name")
        if isinstance(name, str) and name:
            result[name] = tool
    return result


def _snippet_key(snippet: Dict[str, Any]) -> str:
    snippet_id = snippet.get("id")
    if isinstance(snippet_id, str) and snippet_id:
        return f"id:{snippet_id}"
    text = str(snippet.get("text", ""))
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    return f"text_hash:{digest}"


def compute_diff_report(bundle_a: Dict[str, Any], bundle_b: Dict[str, Any]) -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "bundle_a_sha256": _bundle_sha(bundle_a),
        "bundle_b_sha256": _bundle_sha(bundle_b),
        "conversation": {},
        "tools": {},
        "context": {},
        "runtime": {},
    }

    conversation = {}
    for role in ["system", "developer", "user"]:
        a_text = _conversation_text(bundle_a, role)
        b_text = _conversation_text(bundle_b, role)
        conversation[role] = {
            "changed": a_text != b_text,
            "old": a_text,
            "new": b_text,
            "unified_diff": _unified_diff(a_text, b_text, f"a:{role}", f"b:{role}"),
        }
    report["conversation"] = conversation

    tools_a = _tool_map(bundle_a)
    tools_b = _tool_map(bundle_b)
    names_a = set(tools_a)
    names_b = set(tools_b)

    schema_changed = []
    for name in sorted(names_a & names_b):
        old_schema = tools_a[name].get("json_schema", {})
        new_schema = tools_b[name].get("json_schema", {})
        if canonical_json(old_schema) != canonical_json(new_schema):
            old_text = _pretty_json(old_schema)
            new_text = _pretty_json(new_schema)
            schema_changed.append(
                {
                    "tool_name": name,
                    "old_schema": old_schema,
                    "new_schema": new_schema,
                    "unified_diff": _unified_diff(old_text, new_text, f"a:{name}", f"b:{name}"),
                }
            )

    report["tools"] = {
        "added": sorted(names_b - names_a),
        "removed": sorted(names_a - names_b),
        "schema_changed": schema_changed,
    }

    snippets_a = {_snippet_key(s): s for s in (bundle_a.get("context", {}).get("retrieved_snippets", []) or []) if isinstance(s, dict)}
    snippets_b = {_snippet_key(s): s for s in (bundle_b.get("context", {}).get("retrieved_snippets", []) or []) if isinstance(s, dict)}

    keys_a = set(snippets_a)
    keys_b = set(snippets_b)
    report["context"] = {
        "added": sorted(keys_b - keys_a),
        "removed": sorted(keys_a - keys_b),
    }

    constraints_a = (bundle_a.get("runtime", {}) or {}).get("constraints", {}) or {}
    constraints_b = (bundle_b.get("runtime", {}) or {}).get("constraints", {}) or {}
    all_constraint_keys = sorted(set(constraints_a) | set(constraints_b))

    changed: List[Dict[str, Any]] = []
    added: List[str] = []
    removed: List[str] = []
    for key in all_constraint_keys:
        if key not in constraints_a:
            added.append(key)
        elif key not in constraints_b:
            removed.append(key)
        elif constraints_a[key] != constraints_b[key]:
            changed.append({"key": key, "old": constraints_a[key], "new": constraints_b[key]})

    report["runtime"] = {
        "added": added,
        "removed": removed,
        "changed": changed,
    }

    return report


def render_diff_summary(report: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("ModelMirror Pack Diff")
    lines.append("")
    lines.append(f"Bundle A SHA256: {report['bundle_a_sha256']}")
    lines.append(f"Bundle B SHA256: {report['bundle_b_sha256']}")
    lines.append("")

    lines.append("== Conversation Diffs ==")
    for role in ["system", "developer", "user"]:
        section = report["conversation"][role]
        lines.append(f"[{role}] changed: {section['changed']}")
        if section["changed"]:
            lines.extend(section["unified_diff"])
            lines.append("")

    lines.append("== Tools ==")
    lines.append(f"Added: {report['tools']['added']}")
    lines.append(f"Removed: {report['tools']['removed']}")
    if report["tools"]["schema_changed"]:
        for item in report["tools"]["schema_changed"]:
            lines.append(f"Schema changed: {item['tool_name']}")
            lines.extend(item["unified_diff"])
            lines.append("")
    else:
        lines.append("Schema changed: []")

    lines.append("== Context Snippets ==")
    lines.append(f"Added: {report['context']['added']}")
    lines.append(f"Removed: {report['context']['removed']}")

    lines.append("== Runtime Constraints ==")
    lines.append(f"Added keys: {report['runtime']['added']}")
    lines.append(f"Removed keys: {report['runtime']['removed']}")
    lines.append(f"Changed values: {report['runtime']['changed']}")

    return "\n".join(lines)
