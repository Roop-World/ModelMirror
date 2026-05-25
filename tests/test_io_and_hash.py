import re

from model_mirror.io_utils import make_run_id, sha256_of_payload


def test_sha_is_canonical_key_order_independent():
    a = {"b": 1, "a": {"y": 2, "x": 3}}
    b = {"a": {"x": 3, "y": 2}, "b": 1}
    assert sha256_of_payload(a) == sha256_of_payload(b)


def test_run_id_format():
    run_id = make_run_id("20260305T120000Z", "abcdef1234567890")
    assert run_id == "20260305T120000Z__abcdef123456"
    assert re.match(r"^\d{8}T\d{6}Z__[a-f0-9]{12}$", run_id)
