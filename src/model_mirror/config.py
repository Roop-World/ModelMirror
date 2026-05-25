"""Configuration constants for ModelMirror."""

from pathlib import Path

SCHEMA_VERSION = "1.0"
POLL_INTERVAL_SECONDS = 0.25
UI_WAIT_TIMEOUT_SECONDS = 60 * 60 * 8

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs"
SUGGESTION_LIBRARY_PATH = PROJECT_ROOT / "suggestions" / "suggestion_library.json"
