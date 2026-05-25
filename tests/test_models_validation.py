from pydantic import ValidationError

from model_mirror.validation import validate_packed_prompt


def _valid_bundle():
    return {
        "schema_version": "1.0",
        "conversation": {
            "system": "sys",
            "developer": "dev",
            "user": "usr",
        },
        "context": {"retrieved_snippets": []},
        "tools": [],
        "runtime": {"mode": "agent", "constraints": {}},
        "raw": {},
    }


def test_valid_bundle_passes():
    model = validate_packed_prompt(_valid_bundle())
    assert model.schema_version == "1.0"


def test_missing_raw_fails_closed():
    payload = _valid_bundle()
    payload.pop("raw")
    try:
        validate_packed_prompt(payload)
        assert False, "expected validation error"
    except ValidationError:
        assert True


def test_root_extras_forbidden():
    payload = _valid_bundle()
    payload["extra_root"] = "nope"
    try:
        validate_packed_prompt(payload)
        assert False, "expected validation error"
    except ValidationError:
        assert True
