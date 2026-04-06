from __future__ import annotations

import os
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
EXAMPLE_AUDIO_PATH = PROJECT_DIR / "example_meeting.mp3"
DEFAULT_MODEL_SIZE = os.environ.get("MEETING_MODEL_SIZE", "tiny")


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
