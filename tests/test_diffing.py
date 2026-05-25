from model_mirror.diffing import compute_diff_report


def test_diff_groups_required_sections():
    bundle_a = {
        "schema_version": "1.0",
        "conversation": {"system": "A", "developer": "D1", "user": "U"},
        "context": {"retrieved_snippets": [{"id": "s1", "source": "m", "text": "x", "metadata": {}}]},
        "tools": [{"name": "t1", "description": "", "json_schema": {"type": "object", "properties": {"a": {"type": "string"}}}}],
        "runtime": {"mode": "agent", "constraints": {"max_output_tokens": 100}},
        "raw": {},
    }
    bundle_b = {
        "schema_version": "1.0",
        "conversation": {"system": "B", "developer": "D2", "user": "U"},
        "context": {"retrieved_snippets": [{"id": "s2", "source": "m", "text": "y", "metadata": {}}]},
        "tools": [
            {"name": "t1", "description": "", "json_schema": {"type": "object", "properties": {"a": {"type": "string"}, "b": {"type": "number"}}}},
            {"name": "t2", "description": "", "json_schema": {"type": "object"}},
        ],
        "runtime": {"mode": "agent", "constraints": {"max_output_tokens": 200, "model_name": "x"}},
        "raw": {},
    }

    report = compute_diff_report(bundle_a, bundle_b)

    assert report["conversation"]["system"]["changed"] is True
    assert report["conversation"]["developer"]["changed"] is True
    assert report["tools"]["added"] == ["t2"]
    assert report["tools"]["removed"] == []
    assert len(report["tools"]["schema_changed"]) == 1
    assert report["tools"]["schema_changed"][0]["tool_name"] == "t1"
    assert report["context"]["added"] == ["id:s2"]
    assert report["context"]["removed"] == ["id:s1"]
    assert report["runtime"]["added"] == ["model_name"]
