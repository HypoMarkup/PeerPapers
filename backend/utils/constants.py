"""Centralized configuration constants for the backend server and domain logic."""

import json
from pathlib import Path

_SHARED_FILE = Path(__file__).resolve().parents[2] / "shared" / "constants.json"
_CONFIG = json.loads(_SHARED_FILE.read_text(encoding="utf-8"))

# ─── Server & Network ───
DEFAULT_HOST: str = _CONFIG["DEFAULT_HOST"]
DEFAULT_PORT: int = _CONFIG["DEFAULT_PORT"]

# ─── Transport & Limits ───
DEFAULT_SEND_TIMEOUT: float = float(_CONFIG["DEFAULT_SEND_TIMEOUT"])
MAX_MESSAGE_SIZE_BYTES: int = _CONFIG["MAX_MESSAGE_SIZE_BYTES"]

# ─── Room Codes ───
CODE_LENGTH: int = _CONFIG["CODE_LENGTH"]
MAX_CODE_RETRIES: int = _CONFIG["MAX_CODE_RETRIES"]

# ─── Room & Exam Defaults ───
DEFAULT_EXAM_DURATION_MINS: int = _CONFIG["DEFAULT_EXAM_DURATION_MINS"]
