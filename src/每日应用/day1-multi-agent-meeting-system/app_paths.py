from __future__ import annotations

import os
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
EXAMPLE_AUDIO_PATH = PROJECT_DIR / "example_meeting.mp3"
DEFAULT_MODEL_SIZE = os.environ.get("MEETING_MODEL_SIZE", "tiny")
DEFAULT_ACTION_EXTRACTOR = os.environ.get("MEETING_ACTION_EXTRACTOR", "rules").lower()
DEFAULT_ACTION_LLM_MODEL = os.environ.get("MEETING_ACTION_MODEL")
DEFAULT_ACTION_API_KEY = os.environ.get("MEETING_ACTION_API_KEY")
DEFAULT_ACTION_TIMEOUT = int(os.environ.get("MEETING_ACTION_TIMEOUT", "60"))
DEFAULT_ACTION_FALLBACK = os.environ.get("MEETING_ACTION_FALLBACK", "1").lower() not in {"0", "false", "no"}
DEFAULT_OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
DEFAULT_OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL")
DEFAULT_OPENROUTER_BASE_URL = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
DEFAULT_OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_SITE_URL = os.environ.get("OPENROUTER_SITE_URL")
OPENROUTER_APP_NAME = os.environ.get("OPENROUTER_APP_NAME", "ai-daily-challenges")


def resolve_db_path(db_path: str | os.PathLike[str] | None = None) -> Path:
    raw_value = db_path or os.environ.get("MEETING_DB_PATH")
    candidate = Path(raw_value).expanduser() if raw_value else DATA_DIR / "meetings.db"

    if not candidate.is_absolute():
        candidate = (Path.cwd() / candidate).resolve()

    return candidate


def ensure_parent_dir(path: str | os.PathLike[str]) -> Path:
    resolved = Path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved
