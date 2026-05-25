"""JSON and deterministic I/O helpers."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple


def read_json_file(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json_file(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_of_payload(payload: Any) -> str:
    blob = canonical_json(payload).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def utc_now_strings() -> Tuple[str, str]:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    return now.strftime("%Y-%m-%dT%H:%M:%SZ"), now.strftime("%Y%m%dT%H%M%SZ")


def make_run_id(timestamp_compact: str, bundle_sha256: str) -> str:
    return f"{timestamp_compact}__{bundle_sha256[:12]}"


def ensure_run_dir(out_dir: Path, run_id: str) -> Path:
    run_dir = out_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def stable_dict(**kwargs: Any) -> Dict[str, Any]:
    return dict(kwargs)
