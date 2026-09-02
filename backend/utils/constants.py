"""Centralized configuration constants for the backend server and domain logic."""

# ─── Server & Network ───
DEFAULT_HOST: str = "127.0.0.1"
DEFAULT_PORT: int = 8765

# ─── Transport ───
DEFAULT_SEND_TIMEOUT: float = 5.0

# ─── Room Codes ───
CODE_LENGTH: int = 6
MAX_CODE_RETRIES: int = 100

# ─── Room & Exam Defaults ───
DEFAULT_EXAM_DURATION_MINS: int = 15
