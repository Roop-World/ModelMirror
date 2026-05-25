"""Suggestion library loading and selection."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Sequence

from model_mirror.config import SUGGESTION_LIBRARY_PATH
from model_mirror.io_utils import read_json_file
from model_mirror.models import SuggestionEntry


def load_suggestion_library(path: Path | None = None) -> List[SuggestionEntry]:
    source = path or SUGGESTION_LIBRARY_PATH
    if not source.exists():
        return []
    payload = read_json_file(source)
    if not isinstance(payload, list):
        return []

    items: List[SuggestionEntry] = []
    for item in payload:
        try:
            items.append(SuggestionEntry.model_validate(item))
        except Exception:
            continue
    return items


def suggestions_for_codes(codes: Sequence[str], library: Iterable[SuggestionEntry]) -> List[SuggestionEntry]:
    wanted = set(codes)
    selected: List[SuggestionEntry] = []
    seen = set()
    for entry in library:
        if entry.id in seen:
            continue
        if wanted.intersection(entry.applies_to):
            selected.append(entry)
            seen.add(entry.id)
    return selected
