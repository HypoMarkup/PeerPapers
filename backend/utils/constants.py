"""Centralized configuration constants for the backend server and domain logic."""

# ─── Server & Network ───
DEFAULT_HOST: str = "127.0.0.1"
DEFAULT_PORT: int = 8765

# ─── Transport & Limits ───
DEFAULT_SEND_TIMEOUT: float = 5.0
MAX_MESSAGE_SIZE_BYTES: int = 50 * 1024 * 1024  # 50 MB max payload for PDF binary transfers

# ─── Room Codes ───
CODE_LENGTH: int = 6
MAX_CODE_RETRIES: int = 100

# ─── Room & Exam Defaults ───
DEFAULT_EXAM_DURATION_MINS: int = 60
